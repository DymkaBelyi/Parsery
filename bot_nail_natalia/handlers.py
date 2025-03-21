import os
from dotenv import load_dotenv

from aiogram.fsm.state import State, StatesGroup
import sqlite3
from datetime import datetime
from aiogram import Router
from aiogram.types import (CallbackQuery, Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
                           InlineKeyboardMarkup, InlineKeyboardButton, BotCommand, BotCommandScopeChat)
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from other_function import bot
from create_bd import create_available_keyboards, add_appointment

load_dotenv()
ADMIN_IDS = [int(admin_id) for admin_id in os.getenv("ADMINS_NAIL", "").split(",")]

router = Router()


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
        date_keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=date)] for date in available_dates],
                                            resize_keyboard=True)


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
        await message.answer("⛔ У вас нет прав для выполнения этой команды.")


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
    time_buttons.append([KeyboardButton(text="Назад")])  # Добавляем кнопку "Назад"
    time_keyboard = ReplyKeyboardMarkup(keyboard=time_buttons, resize_keyboard=True)
    await message.answer("Выберите время:", reply_markup=time_keyboard)
    await state.set_state(AdminState.time)


@router.message(AdminState.time)
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
        cursor.execute("SELECT * FROM appointments WHERE date = ? AND time = ?",
                       (selected_date, selected_time))
        existing_appointment = cursor.fetchone()

    if existing_appointment:
        await message.answer("Извините, это время уже занято. Пожалуйста, выберите другое время.")
    else:
        add_appointment(user_data["name"], user_data["phone"], selected_date, selected_time,
                        user_id=None)  # user_id=None для клиентов
        confirmation_text = (
            f"✅ Запись подтверждена!\n📅 Дата: {datetime.strptime(selected_date, '%d-%m-%Y').strftime(
                '%d-%m-%Y')}\n⏰ "
            f"Время: {selected_time}\n👤 Имя: {user_data['name']}\n📞 Телефон: {user_data['phone']}\n\nЖдём вас! 🚗💅"
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

    await message.answer("Привет! Я бот для записи на маникюр 💅✨ Выбери удобное время, и я все запомню! Давай начнем! "
                         "Введите ваше имя:")
    await state.set_state(Booking.name)

    # Определяем команды для пользователей и администраторов
    user_commands = [
        BotCommand(command="start", description="Начать запись"),
        BotCommand(command="cancel", description="Удалить запись"),
    ]

    admin_commands = user_commands + [
        BotCommand(command="list_day", description="Проверить записи, для администраторов"),
        BotCommand(command="all_list", description="Посмотреть все записи, только для администратора"),
        BotCommand(command="admin_book", description="Запись на маникюр для администратора"),
    ]

    # Устанавливаем команды: для обычных пользователей и отдельно для админов
    if message.from_user.id in ADMIN_IDS:
        await bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=message.chat.id))
    else:
        await bot.set_my_commands(user_commands, scope=BotCommandScopeChat(chat_id=message.chat.id))


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

    time_buttons = [[KeyboardButton(text=time)] for time in available_times]
    time_buttons.append([KeyboardButton(text="Назад")])  # Добавляем кнопку "Назад"
    time_keyboard = ReplyKeyboardMarkup(keyboard=time_buttons, resize_keyboard=True)
    await message.answer("Выберите время:", reply_markup=time_keyboard)
    await state.set_state(Booking.time)


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


# Обработчик команды "list_day", чтобы администратор мог вводить любую дату и посмотреть записи
@router.message(Command("list_day"))
async def view_appointments(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in ADMIN_IDS:
        await message.answer("Введите дату в формате DD-MM-YYYY для просмотра записей на эту дату.")
        await state.set_state(AdminState.view_date)  # Устанавливаем новое состояние
    else:
        await message.answer("⛔ У вас нет прав для выполнения этой команды.")


@router.message(Command("all_list"))
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
            await message.answer("📌 Записей пока нет.")
            return

        response_text = "📋 **Список всех записей:**\n\n"
        count = 0

        for date, time, name, phone in appointments:
            response_text += (f"📅 {datetime.strptime(date, '%d-%m-%Y').strftime('%d-%m-%Y')} \n"
                              f"⏰ {time}\n👤 {name}\n 📞 {phone}\n\n")
            count += 1

            if count % 10 == 0:  # Каждые 10 записей отправляем сообщение
                await message.answer(response_text)
                response_text = ""

        if response_text:
            await message.answer(response_text)

    except sqlite3.Error as e:
        print(f"[Ошибка БД] {e}")  # Вывод ошибки в консоль
        await message.answer("❌ Произошла ошибка при получении списка записей.")

conn = sqlite3.connect("appointments.db")
cursor = conn.cursor()


# Обработчик введённой даты
@router.message(AdminState.view_date)
async def handle_admin_date(message: Message, state: FSMContext):
    date_input = message.text.strip()

    try:
        datetime.strptime(date_input, "%d-%m-%Y")
    except ValueError:
        await message.answer("Ошибка! Неверный формат даты. Пожалуйста, введите дату в формате DD-MM-YYYY.")
        return

    with sqlite3.connect("appointments.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, user_id, name, phone, date, time FROM appointments WHERE date = ? ORDER BY time ASC",
                       (date_input,))
        appointments = cursor.fetchall()

    if appointments:
        appointments_text = "\n\n".join(
            [f"ID: {id}\n👤 Имя: {name}\n📞 Телефон: {phone}\n📅 Дата: "
             f"{datetime.strptime(date, '%d-%m-%Y').strftime('%d-%m-%Y')}\n⏰ Время: {time}"
             for id, user_id, name, phone, date, time in appointments]
        )
        await message.answer(f"Записи на {date_input}:\n{appointments_text}")
    else:
        await message.answer(f"На {date_input} нет записей.")

    await state.clear()  # Очищаем состояние после просмотра записей


# Обработчик удаления записи на маникюр
@router.message(Command("cancel"))
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

            # Если записей несколько – предлагаем выбрать
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=f"{date} {time}", callback_data=f"cancel_{appointment_id}")]
                    for appointment_id, date, time in appointments
                ]
            )
            await message.answer("Выберите запись, которую хотите отменить:", reply_markup=keyboard)

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        await message.answer("❌ Ошибка при отмене записи. Попробуйте позже.")

    await state.clear()


# Обработчик кнопки отмены записи
@router.callback_query(lambda c: c.data.startswith("cancel_"))
async def process_cancel_callback(callback_query: CallbackQuery):
    appointment_id = int(callback_query.data.split("_")[1])

    try:
        with sqlite3.connect("appointments.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT date, time FROM appointments WHERE id = ?", (appointment_id,))
            appointment = cursor.fetchone()

            if not appointment:
                await callback_query.answer("⚠ Запись не найдена.", show_alert=True)
                return

            appointment_date, appointment_time = appointment

            # Удаляем запись
            cursor.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
            conn.commit()

            await callback_query.message.edit_text(f"❌ Запись на {appointment_date} в {appointment_time} отменена.")

            # Оповещение админов, если отмена в день приёма
            today_date = datetime.now().strftime("%d-%m-%Y")
            if appointment_date == today_date:
                alert_text = (f"<b>❗ Клиент отменил запись в день приёма ❗</b>\n"
                              f"📅 Дата: {appointment_date}\n⏰ Время: {appointment_time}")
                for admin_id in ADMIN_IDS:
                    await bot.send_message(admin_id, alert_text, parse_mode="HTML")

            update_available_dates()

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        await callback_query.answer("❌ Ошибка при отмене записи.", show_alert=True)

    await callback_query.answer()


@router.message(Command("delete"))
async def delete_appointment_by_id(message: Message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        await message.answer("⛔ У вас нет прав для выполнения этой команды.")
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

        await message.answer(f"✅ Запись ID {appointment_id} ({appointment[1]}, {datetime.strptime(
            appointment[2], '%d-%m-%Y').strftime('%d-%m-%Y')} в {appointment[3]}) удалена.")

    update_available_dates()