from dotenv import load_dotenv
import os
import sqlite3
from datetime import datetime

from aiogram import Router, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from keyboards import admin_kb, cancel_keyboard_admin
from handlers import available_dates, available_times_for_dates, date_keyboard, update_available_dates
from create_bd import add_appointment

load_dotenv()
ADMIN_IDS = [int(admin_id) for admin_id in os.getenv("ADMINS_NAIL", "").split(",")]

admin_router = Router()


# Машина состояний для обработки даты
class AdminState(StatesGroup):
	view_date = State()  # Добавляем новое состояние для просмотра записей
	name = State()
	phone = State()
	date = State()
	time = State()


# Добавили обработки удаления
class DeleteState(StatesGroup):
	waiting_for_date = State()
	waiting_for_id = State()


@admin_router.message(F.text == "❌ Отмена записи")
async def cancel_handler(message: Message, state: FSMContext):
	await state.clear()
	await message.answer("Запись отменена, выбери пункт из меню", reply_markup=admin_kb)


@admin_router.message(F.text == "📝 Записать на маникюр")
async def admin_book(message: Message, state: FSMContext):
	if not available_dates:
		await message.answer("В данный момент нет свободных мест. Попробуйте записаться немного позже.")
		return

	user_id = message.from_user.id
	if user_id in ADMIN_IDS:
		await state.set_state(AdminState.name)
		await message.answer("Введите имя клиента:", reply_markup=cancel_keyboard_admin)
	else:
		await message.answer("⛔ У вас нет прав для выполнения этой команды.")


@admin_router.message(AdminState.name)
async def admin_get_name(message: Message, state: FSMContext):
	if message.text == "❌ Отмена записи":
		return await cancel_handler(message, state)

	await state.update_data(name=message.text)
	await state.set_state(AdminState.phone)
	await message.answer("Введите номер телефона клиента:", reply_markup=cancel_keyboard_admin)


@admin_router.message(AdminState.phone)
async def admin_get_phone(message: Message, state: FSMContext):
	if message.text == "❌ Отмена записи":
		return await cancel_handler(message, state)
	await state.update_data(phone=message.text)
	await state.set_state(AdminState.date)
	await message.answer("Выберите дату:", reply_markup=date_keyboard)


@admin_router.message(AdminState.date)
async def admin_get_date(message: Message, state: FSMContext):
	selected_date = message.text.strip()
	update_available_dates()  # Обновляем список дат перед выбором

	if selected_date not in available_dates:
		await message.answer("Ошибка! Выбранная дата недоступна. Пожалуйста, выберите другую.")
		return

	await state.update_data(date=selected_date)
	available_times = available_times_for_dates.get(selected_date, [])

	if not available_times:
		await message.answer("На эту дату нет доступного времени. Выберите другую дату.")
		return

	time_buttons = [[KeyboardButton(text=time)] for time in available_times]
	time_buttons.append(
		[KeyboardButton(text="Назад"), KeyboardButton(text="❌ Отмена записи")]
	)  # Добавляем кнопку "Назад"
	time_keyboard = ReplyKeyboardMarkup(keyboard=time_buttons, resize_keyboard=True)
	await state.set_state(AdminState.time)
	await message.answer("Выберите время:", reply_markup=time_keyboard)


@admin_router.message(AdminState.time)
async def admin_get_time(message: Message, state: FSMContext):
	user_data = await state.get_data()
	selected_time = message.text.strip()

	if selected_time == "Назад":
		await message.answer("Выберите дату:", reply_markup=date_keyboard)
		await state.set_state(AdminState.date)
		return

	selected_date = user_data.get("date")

	try:
		datetime.strptime(selected_time, "%H:%M")
	except ValueError:
		await message.answer("Ошибка! Выбранное время некорректно. Пожалуйста, выберите доступное время.")
		return

	with sqlite3.connect("appointments.db") as conn:
		cursor = conn.cursor()
		cursor.execute(
			"SELECT * FROM appointments WHERE date = ? AND time = ?",
			(selected_date, selected_time)
		)
		existing_appointment = cursor.fetchone()

	if existing_appointment:
		await message.answer("Извините, это время уже занято. Пожалуйста, выберите другое время.")
	else:
		add_appointment(
			user_data["name"], user_data["phone"], selected_date, selected_time,
			user_id=None
		)  # user_id=None для клиентов
		confirmation_text = (
			f"✅ Запись подтверждена!\n📅 Дата: {datetime.strptime(selected_date, '%d-%m-%Y').strftime(
				'%d-%m-%Y'
			)}\n⏰ "
			f"Время: {selected_time}\n👤 Имя: {user_data['name']}\n📞 Телефон: {user_data['phone']}\n\nЖдём вас! 🚗💅"
		)
		await message.answer(confirmation_text, reply_markup=admin_kb)
		await state.clear()

		# Обновляем клавиатуру с доступными датами и временем
		update_available_dates()


# Обработчик введённой даты
@admin_router.message(AdminState.view_date)
async def handle_admin_date(message: Message, state: FSMContext):
	date_input = message.text.strip()

	try:
		datetime.strptime(date_input, "%d-%m-%Y")
	except ValueError:
		await message.answer("Ошибка! Неверный формат даты. Пожалуйста, введите дату в формате DD-MM-YYYY.")
		return

	with sqlite3.connect("appointments.db") as conn:
		cursor = conn.cursor()
		cursor.execute(
			"SELECT id, user_id, name, phone, date, time FROM appointments WHERE date = ? ORDER BY time ASC",
			(date_input,)
		)
		appointments = cursor.fetchall()

	if appointments:
		appointments_text = "\n\n".join(
			[f"ID: {id}\n👤 Имя: {name}\n📞 Телефон: {phone}\n📅 Дата: "
			 f"{datetime.strptime(date, '%d-%m-%Y').strftime('%d-%m-%Y')}\n⏰ Время: {time}"
			 for id, user_id, name, phone, date, time in appointments]
		)
		await message.answer(f"Записи на {date_input}:\n{appointments_text}", reply_markup=admin_kb)
	else:
		await message.answer(f"На {date_input} нет записей.")

	await state.clear()  # Очищаем состояние после просмотра записей


@admin_router.message(F.text == "❌ Удалить запись")
async def start_delete(message: Message, state: FSMContext):
	user_id = message.from_user.id
	if user_id not in ADMIN_IDS:
		await message.answer("⛔ У вас нет прав для выполнения этой команды.")
		return

	await message.answer(
		"Введите дату в формате DD-MM-YYYY, чтобы посмотреть записи на этот день.",
		reply_markup=ReplyKeyboardRemove()
	)
	await state.set_state(DeleteState.waiting_for_date)


# Обработчик ввода даты
@admin_router.message(DeleteState.waiting_for_date)
async def get_appointments_by_date(message: Message, state: FSMContext):
	try:
		date_str = message.text
		datetime.strptime(date_str, "%d-%m-%Y")  # Проверяем формат даты

		with sqlite3.connect("appointments.db") as conn:
			cursor = conn.cursor()
			cursor.execute(
				"SELECT id, name, phone, date, time FROM appointments WHERE date = ? ORDER BY time",
				(date_str,)
			)
			appointments = cursor.fetchall()

		if not appointments:
			await message.answer("❌ На эту дату нет записей.", reply_markup=admin_kb)
			await state.clear()
			return

		response = f"📅 *Записи на {date_str}:*\n\n"
		for appointment in appointments:
			response += (
				f"*ID:* {appointment[0]}\n"
				f"👤 *Имя:* {appointment[1]}\n"
				f"📞 *Телефон:* {appointment[2]}\n"
				f"📆 *Дата:* {appointment[3]}\n"
				f"⏰ *Время:* {appointment[4]}\n\n"
			)

		await message.answer(response, parse_mode="Markdown")
		await message.answer("✏ Введите *ID записи*, которую хотите удалить.")
		await state.update_data(date=date_str)
		await state.set_state(DeleteState.waiting_for_id)

	except ValueError:
		await message.answer("⚠ Неверный формат даты. Введите в формате *DD-MM-YYYY*.")


@admin_router.message(DeleteState.waiting_for_id)
async def delete_appointment_by_id(message: Message, state: FSMContext):
	try:
		appointment_id = int(message.text)
	except ValueError:
		await message.answer("⚠ ID должен быть числом.")
		return

	with sqlite3.connect("appointments.db") as conn:
		cursor = conn.cursor()
		cursor.execute("SELECT id, name, date, time FROM appointments WHERE id = ?", (appointment_id,))
		appointment = cursor.fetchone()

		if not appointment:
			await message.answer("❌ Запись с таким ID не найдена.")
			return

		cursor.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
		conn.commit()

		await message.answer(
			f"✅ Запись *ID {appointment_id}* удалена:\n"
			f"👤 *Имя:* {appointment[1]}\n"
			f"📆 *Дата:* {appointment[2]}\n"
			f"⏰ *Время:* {appointment[3]}",
			parse_mode="Markdown", reply_markup=admin_kb
		)

	await state.clear()
	update_available_dates()


@admin_router.message(F.text == "📜 Посмотреть все записи")
async def all_appointments(message: Message):
	user_id = message.from_user.id
	if user_id not in ADMIN_IDS:
		await message.answer("⛔ У вас нет прав для выполнения этой команды.")
		return

	try:
		with sqlite3.connect("appointments.db") as conn:
			cursor = conn.cursor()
			cursor.execute("SELECT date, time, name, phone FROM appointments ORDER BY date, time")
			appointments = cursor.fetchall()

		if not appointments:
			await message.answer("📌 Записей пока нет.", reply_markup=admin_kb)
			return

		response_text = "📋 **Список всех записей:**\n\n"
		count = 0

		for date, time, name, phone in appointments:
			response_text += (f"📅 {datetime.strptime(date, '%d-%m-%Y').strftime('%d-%m-%Y')} \n"
							  f"⏰ {time}\n👤 {name}\n 📞 {phone}\n\n")
			count += 1

			if count % 10 == 0:  # Каждые 10 записей отправляем сообщение
				await message.answer(response_text, reply_markup=admin_kb)
				response_text = ""

		if response_text:
			await message.answer(response_text, reply_markup=admin_kb)

		# Отправим итоговое сообщение с количеством записей
		total = len(appointments)
		await message.answer(f"📊 Всего записей: {total}", reply_markup=admin_kb)

	except sqlite3.Error as e:
		print(f"[Ошибка БД] {e}")  # Вывод ошибки в консоль
		await message.answer("❌ Произошла ошибка при получении списка записей.")


conn = sqlite3.connect("appointments.db")
cursor = conn.cursor()
