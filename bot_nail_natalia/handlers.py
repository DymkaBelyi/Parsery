import os
from dotenv import load_dotenv

from aiogram.fsm.state import State, StatesGroup
import sqlite3
from aiogram import types
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, BotCommandScopeChat
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from other_function import bot
from create_bd import create_available_keyboards, add_appointment
from keyboards import admin_kb, user_kb, cancel_keyboard

load_dotenv()
ADMIN_IDS = [int(admin_id) for admin_id in os.getenv("ADMINS_NAIL", "").split(",")]

router = Router()


class Booking(StatesGroup):
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
        date_keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=date)] for date in available_dates],
                                            resize_keyboard=True)


@router.message(F.text == "❌ Прекратить запись")
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Запись отменена. Если передумаете — просто нажмите «💅 Записаться на маникюр» снова.",
                         reply_markup=user_kb)


# Обновление клавиатуры с доступными датами
available_dates, available_times_for_dates = create_available_keyboards()
# Проверка на наличие доступных дат
if not available_dates:
    date_keyboard = None
else:
    date_keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=date)] for date in available_dates],
                                        resize_keyboard=True)


@router.message(CommandStart())
async def cmd_start(message: Message):
    # Добавляем команду /start в меню для всех пользователей
    await bot.set_my_commands(
        [types.BotCommand(command="/start", description="Нажми на старт и меню появится")],
        scope=BotCommandScopeChat(chat_id=message.chat.id)
    )

    if message.from_user.id in ADMIN_IDS:
        # Убираем команды меню у админов
        await bot.set_my_commands([], scope=BotCommandScopeChat(chat_id=message.chat.id))
        await message.answer('Админ панель: ', reply_markup=admin_kb)
    else:
        await message.answer(
            "Привет! Я бот для записи на маникюр 💅✨ Выбери удобное время, и я все запомню! Давай начнем!",
            reply_markup=user_kb
        )


@router.message(F.text == "💅 Записаться на маникюр")
async def list_create(message: Message, state: FSMContext):
    if not available_dates:
        await message.answer("Извините, в данный момент нет свободных мест. Попробуйте записаться немного позже.")
        return

    if message.text == "❌ Прекратить запись":
        return await cancel_handler(message, state)

    await state.set_state(Booking.name)
    await message.answer('Введите ваше имя для записи: ', reply_markup=cancel_keyboard)


@router.message(Booking.name)
async def get_name(message: Message, state: FSMContext):
    if message.text == "❌ Прекратить запись":
        return await cancel_handler(message, state)

    await state.update_data(name=message.text)
    await state.set_state(Booking.phone)
    await message.answer("Введите ваш номер телефона:", reply_markup=cancel_keyboard)


@router.message(Booking.phone)
async def get_phone(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await state.update_data(phone=message.text, user_id=user_id)
    await state.set_state(Booking.date)
    await message.answer("Выберите дату:", reply_markup=date_keyboard)


@router.message(Booking.date)
async def get_date(message: Message, state: FSMContext):
    update_available_dates()  # Обновляем список дат перед выбором

    if not available_dates:
        await message.answer("Извините, в данный момент нет свободных мест. Попробуйте записаться немного позже.")
        return

    selected_date = message.text.strip()

    await state.update_data(date=selected_date)
    available_times = available_times_for_dates.get(selected_date, [])

    if not available_times:
        await message.answer("На эту дату нет доступного времени. Выберите другую дату.")
        return

    if message.text == "❌ Прекратить запись":
        return await cancel_handler(message, state)

    time_buttons = [[KeyboardButton(text=time)] for time in available_times]
    time_buttons.append([KeyboardButton(text="Назад"), KeyboardButton(text="❌ Прекратить запись")])
    time_keyboard = ReplyKeyboardMarkup(keyboard=time_buttons, resize_keyboard=True)
    await state.set_state(Booking.time)
    await message.answer("Выберите время:", reply_markup=time_keyboard)


@router.message(Booking.time)
async def get_time(message: Message, state: FSMContext):
    user_data = await state.get_data()
    selected_time = message.text.strip()

    if selected_time == "Назад":
        await message.answer("Выберите дату:", reply_markup=date_keyboard)
        await state.set_state(Booking.date)
        return

    selected_date = user_data.get("date")
    user_id = message.from_user.id  # Получаем user_id из сообщения

    try:
        datetime.strptime(selected_time, "%H:%M")
    except ValueError:
        await message.answer("Ошибка! Выбранное время некорректно. Пожалуйста, выберите доступное время.")
        return

    # Проверяем, доступно ли это время
    if not add_appointment(user_data["name"], user_data["phone"], selected_date, selected_time,
                           user_id):
        await message.answer(
            "У вас уже есть активная запись. Пожалуйста, отмените её, прежде чем создавать новую.",
            reply_markup=user_kb
        )
        await state.clear()  # Сбрасываем состояние, чтобы избежать ошибки в будущем
        return

    confirmation_text = (
        f"✅ Запись подтверждена!\n📅 Дата: {selected_date}\n⏰ Время: {selected_time}\n"
        f"👤 Имя: {user_data['name']}\n📞 Телефон: {user_data['phone']}\n\nЖдём вас! 🚗💅"
    )
    await message.answer(confirmation_text, reply_markup=user_kb)
    await state.clear()

    # Обновляем клавиатуру с доступными датами и временем
    update_available_dates()


# Обработчик удаления записи на маникюр
@router.message(F.text == "❌ Отменить запись")
async def cancel_appointment(message: Message, state: FSMContext):
    user_id = message.from_user.id
    today_date = datetime.now().strftime("%d-%m-%Y")

    db_path = "appointments.db"
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, date, time FROM appointments WHERE user_id = ?", (user_id,))
            appointments = cursor.fetchall()  # Получаем все записи пользователя

            if not appointments:
                await message.answer("⚠ У вас нет активных записей.")
                return

            # Если одна запись – удаляем сразу
            if len(appointments) == 1:
                appointment_id, appointment_date, appointment_time = appointments[0]

                cursor.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
                conn.commit()

                await message.answer(f"❌ Ваша запись на {appointment_date} в {appointment_time} отменена.")

                # Оповещение админов, если запись на сегодня
                if appointment_date == today_date:
                    alert_text = (f"<b>❗ Клиент отменил запись в день приёма ❗</b>\n"
                                  f"📅 Дата: {appointment_date}\n⏰ Время: {appointment_time}")
                    for admin_id in ADMIN_IDS:
                        await bot.send_message(admin_id, alert_text, parse_mode="HTML")

                update_available_dates()
                await state.clear()
                return

            # Если записей несколько – предлагаем выбрать через Reply-клавиатуру
            buttons = [[KeyboardButton(text=f"❌ Отменить {date} {time}")] for _, date, time in appointments]
            buttons.append([KeyboardButton(text="🔙 Назад")])  # Кнопка "Отмена" на отдельной строке
            keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

            await message.answer("Выберите запись, которую хотите отменить:", reply_markup=keyboard)

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        await message.answer("❌ Ошибка при отмене записи. Попробуйте позже.")

    await state.clear()


# Обработчик кнопки "🔙 Назад"
@router.message(F.text == "🔙 Назад")
async def cancel_cancel(message: Message, state: FSMContext):
    await message.answer("🚫Хотите выбрать ещё что-то?", reply_markup=user_kb)
    await state.clear()


# Обработчик выбора записи через Reply-клавиатуру
@router.message(F.text.startswith("❌ Отменить "))
async def process_cancel_reply(message: Message):
    text = message.text.replace("❌ Отменить ", "")  # Убираем лишний текст
    try:
        appointment_date, appointment_time = text.split()  # Разбиваем на дату и время

        with sqlite3.connect("appointments.db") as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM appointments WHERE date = ? AND time = ? AND user_id = ?",
                           (appointment_date, appointment_time, message.from_user.id))
            conn.commit()

        await message.answer(f"❌ Запись на {appointment_date} в {appointment_time} отменена.", reply_markup=user_kb)

        # Оповещение админов, если отмена в день приёма
        today_date = datetime.now().strftime("%d-%m-%Y")
        if appointment_date == today_date:
            alert_text = (f"<b>❗ Клиент отменил запись в день приёма ❗</b>\n"
                          f"📅 Дата: {appointment_date}\n⏰ Время: {appointment_time}")
            for admin_id in ADMIN_IDS:
                await bot.send_message(admin_id, alert_text, parse_mode="HTML")

        update_available_dates()

    except ValueError:
        await message.answer("⚠ Неправильный формат. Попробуйте снова.")

