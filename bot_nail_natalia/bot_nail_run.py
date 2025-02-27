import os
from dotenv import load_dotenv

import asyncio
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.state import State, StatesGroup
import sqlite3
from datetime import datetime

from create_bd import create_available_keyboards, add_appointment
from other_function import send_reminders, delete_old_appointments


load_dotenv()
TOKEN = os.getenv("TOKEN_NAIL")

dp = Dispatcher()
bot = Bot(TOKEN)
router = Router()

ADMIN_IDS = [int(admin_id) for admin_id in os.getenv("ADMINS_NAIL", "").split(",")]


class Booking(StatesGroup):
    name = State()
    phone = State()
    date = State()
    time = State()


# Машина состояний для обработки даты
class AdminState(StatesGroup):
    view_date = State()  # Добавляем новое состояние для просмотра записей
    name = State()
    phone = State()
    date = State()
    time = State()


# Обновляем клавиатуру с доступными датами и временем
def update_available_dates():
    global available_dates, available_times_for_dates, date_keyboard
    available_dates, available_times_for_dates = create_available_keyboards()
    if available_dates is None:
        date_keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Нет свободных дат")]], resize_keyboard=True)
    else:
        date_keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=date)] for date in available_dates], resize_keyboard=True)


@router.message(Command("admin_book"))
async def admin_book(message: Message, state: FSMContext):
    if not available_dates:
        await message.answer("Извините, в данный момент нет свободных мест. Попробуйте записаться немного позже.")
        return

    user_id = message.from_user.id
    if user_id in ADMIN_IDS:
        await message.answer("Введите имя клиента:")
        await state.set_state(AdminState.name)
    else:
        await message.answer("У вас нет прав для выполнения этой команды.")


@router.message(AdminState.name)
async def admin_get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите номер телефона клиента:")
    await state.set_state(AdminState.phone)


@router.message(AdminState.phone)
async def admin_get_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("Выберите дату:", reply_markup=date_keyboard)
    await state.set_state(AdminState.date)


@router.message(AdminState.date)
async def admin_get_date(message: Message, state: FSMContext):
    selected_date = message.text.strip()

    if selected_date not in available_dates:
        await message.answer("Ошибка! Выбранная дата недоступна. Пожалуйста, выберите другую.")
        return

    await state.update_data(date=selected_date)
    available_times = available_times_for_dates.get(selected_date, [])

    if not available_times:
        await message.answer("На эту дату нет доступного времени. Выберите другую дату.")
        return

    time_buttons = [[KeyboardButton(text=time)] for time in available_times]
    time_keyboard = ReplyKeyboardMarkup(keyboard=time_buttons, resize_keyboard=True)
    await message.answer("Выберите время:", reply_markup=time_keyboard)
    await state.set_state(AdminState.time)


@router.message(AdminState.time)
async def admin_get_time(message: Message, state: FSMContext):
    user_data = await state.get_data()
    selected_time = message.text.strip()
    selected_date = user_data.get("date")

    try:
        datetime.strptime(selected_time, "%H:%M")
    except ValueError:
        await message.answer("Ошибка! Выбранное время некорректно. Пожалуйста, выберите доступное время.")
        return

    with sqlite3.connect("appointments.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM appointments WHERE date = ? AND time = ?",
                       (selected_date, selected_time))
        existing_appointment = cursor.fetchone()

    if existing_appointment:
        await message.answer("Извините, это время уже занято. Пожалуйста, выберите другое время.")
    else:
        add_appointment(user_data["name"], user_data["phone"], selected_date, selected_time,
                        user_id=None)  # user_id=None для клиентов
        confirmation_text = (
            f"✅ Запись подтверждена!\n📅 Дата: {selected_date}\n⏰ Время: {selected_time}\n"
            f"👤 Имя: {user_data['name']}\n📞 Телефон: {user_data['phone']}\n\nЖдём вас! 🚗💅"
        )
        await message.answer(confirmation_text, reply_markup=ReplyKeyboardRemove())
        await state.clear()

        # Обновляем клавиатуру с доступными датами и временем
        update_available_dates()


# Обновление клавиатуры с доступными датами
available_dates, available_times_for_dates = create_available_keyboards()
# Проверка на наличие доступных дат
if not available_dates:
    date_keyboard = None
else:
    date_keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=date)] for date in available_dates],
                                        resize_keyboard=True)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    if not available_dates:
        await message.answer("Извините, в данный момент нет свободных мест. Попробуйте записаться немного позже.")
        return

    await message.answer("Привет! Я бот для записи на маникюр. Введите ваше имя:")
    await state.set_state(Booking.name)


@router.message(Booking.name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите ваш номер телефона:")
    await state.set_state(Booking.phone)


@router.message(Booking.phone)
async def get_phone(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await state.update_data(phone=message.text, user_id=user_id)
    await message.answer("Выберите дату:", reply_markup=date_keyboard)
    await state.set_state(Booking.date)


@router.message(Booking.date)
async def get_date(message: Message, state: FSMContext):
    if not available_dates:
        await message.answer("Извините, в данный момент нет свободных мест. Попробуйте записаться немного позже.")
        return

    selected_date = message.text.strip()

    if selected_date not in available_dates:
        await message.answer("Ошибка! Выбранная дата недоступна. Пожалуйста, выберите другую.")
        return

    await state.update_data(date=selected_date)
    available_times = available_times_for_dates.get(selected_date, [])

    if not available_times:
        await message.answer("На эту дату нет доступного времени. Выберите другую дату.")
        return

    time_buttons = [[KeyboardButton(text=time)] for time in available_times]
    time_keyboard = ReplyKeyboardMarkup(keyboard=time_buttons, resize_keyboard=True)
    await message.answer("Выберите время:", reply_markup=time_keyboard)
    await state.set_state(Booking.time)


@router.message(Booking.time)
async def get_time(message: Message, state: FSMContext):
    user_data = await state.get_data()
    selected_time = message.text.strip()
    selected_date = user_data.get("date")
    user_id = message.from_user.id  # Получаем user_id из сообщения

    try:
        datetime.strptime(selected_time, "%H:%M")
    except ValueError:
        await message.answer("Ошибка! Выбранное время некорректно. Пожалуйста, выберите доступное время.")
        return

    # Проверяем, доступно ли это время
    if not add_appointment(user_data["name"], user_data["phone"], selected_date, selected_time, user_id):
        await message.answer(
            "У вас уже есть активная запись. Пожалуйста, отмените её, прежде чем создавать новую.",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()  # Сбрасываем состояние, чтобы избежать ошибки в будущем
        return

    confirmation_text = (
        f"✅ Запись подтверждена!\n📅 Дата: {selected_date}\n⏰ Время: {selected_time}\n"
        f"👤 Имя: {user_data['name']}\n📞 Телефон: {user_data['phone']}\n\nЖдём вас! 🚗💅"
    )
    await message.answer(confirmation_text, reply_markup=ReplyKeyboardRemove())
    await state.clear()

    # Обновляем клавиатуру с доступными датами и временем
    update_available_dates()


# Обработчик команды "ist", чтобы администратор мог вводить любую дату и посмотреть записи
@router.message(Command("list"))
async def view_appointments(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in ADMIN_IDS:
        await message.answer("Введите дату в формате YYYY-MM-DD для просмотра записей на эту дату.")
        await state.set_state(AdminState.view_date)  # Устанавливаем новое состояние
    else:
        await message.answer("У вас нет прав для выполнения этой команды.")


conn = sqlite3.connect("appointments.db")
cursor = conn.cursor()


# Обработчик введённой даты
@router.message(AdminState.view_date)
async def handle_admin_date(message: Message, state: FSMContext):
    date_input = message.text.strip()

    try:
        datetime.strptime(date_input, "%Y-%m-%d")
    except ValueError:
        await message.answer("Ошибка! Неверный формат даты. Пожалуйста, введите дату в формате YYYY-MM-DD.")
        return

    with sqlite3.connect("appointments.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, user_id, name, phone, date, time FROM appointments WHERE date = ? ORDER BY time ASC",
                       (date_input,))
        appointments = cursor.fetchall()

    if appointments:
        appointments_text = "\n\n".join(
            [f"ID: {id}\n👤 Имя: {name}\n📞 Телефон: {phone}\n📅 Дата: {date}\n⏰ Время: {time}"
             for id, user_id, name, phone, date, time in appointments]
        )
        await message.answer(f"Записи на {date_input}:\n{appointments_text}")
    else:
        await message.answer(f"На {date_input} нет записей.")

    await state.clear()  # Очищаем состояние после просмотра записей


# Обработчик удаления записи на маникюр
@router.message(Command("cancel"))
async def cancel_appointment(message: Message, state: FSMContext):
    user_id = message.from_user.id  # Получаем ID пользователя

    # Проверяем, есть ли запись у пользователя
    db_path = "appointments.db"
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, date, time FROM appointments WHERE user_id = ?", (user_id,))
            appointment = cursor.fetchone()

            if appointment:
                # Удаляем запись
                cursor.execute("DELETE FROM appointments WHERE id = ?", (appointment[0],))
                conn.commit()

                # Сообщаем пользователю
                cancellation_text = f"❌ Ваша запись на {appointment[1]} в {appointment[2]} отменена."
                await message.answer(cancellation_text)
                update_available_dates()
            else:
                await message.answer("⚠ У вас нет активной записи.")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        await message.answer("Произошла ошибка при отмене записи. Пожалуйста, попробуйте позже.")

    await state.clear()  # Очищаем состояние после команды удаления


@router.message(Command("delete"))
async def delete_appointment_by_id(message: Message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        await message.answer("У вас нет прав для выполнения этой команды.")
        return

    command_parts = message.text.split()
    if len(command_parts) < 2:
        await message.answer("⚠ Введите команду в формате: /delete <ID_записи>\nПример: `/delete 5`",
                             parse_mode="MarkdownV2")
        return

    appointment_id = command_parts[1]

    try:
        appointment_id = int(appointment_id)
    except ValueError:
        await message.answer("⚠ ID должен быть числом. Попробуйте снова.")
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

        await message.answer(f"✅ Запись ID {appointment_id} ({appointment[1]}, {appointment[2]} в {appointment[3]}) удалена.")

    update_available_dates()


# Основной запуск бота
async def main():
    dp.include_router(router)

    # Запуск фонового процесса для отправки напоминаний
    asyncio.create_task(send_reminders())

    # Фоновая задача удаления старых записей
    asyncio.create_task(delete_old_appointments())
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())