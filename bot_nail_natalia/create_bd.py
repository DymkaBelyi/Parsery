import sqlite3
import os
from datetime import datetime, timedelta

MAX_SLOTS_PER_DAY = 5


# Инициализация базы данных
def init_db():
    # Проверяем, существует ли файл БД
    if not os.path.exists("appointments.db"):  # ✅ Фикс: не пересоздаём, если уже есть
        with sqlite3.connect("appointments.db") as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS appointments (
                               id INTEGER PRIMARY KEY AUTOINCREMENT,
                               user_id INTEGER,
                               name TEXT,
                               phone TEXT,
                               date TEXT,
                               time TEXT)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS schedule (
                               date TEXT PRIMARY KEY,
                               max_slots INTEGER)''')
            conn.commit()


init_db()


# Функция для добавления дат в расписание
def add_schedule_dates():
    with sqlite3.connect("appointments.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM schedule")
        count = cursor.fetchone()[0]

        if count == 0:
            for i in range(30):
                date = (datetime.now() + timedelta(days=i)).strftime("%d-%m-%Y")
                cursor.execute("INSERT OR IGNORE INTO schedule (date, max_slots) VALUES (?, ?)",
                               (date, MAX_SLOTS_PER_DAY))
            conn.commit()


add_schedule_dates()


# Функция для получения занятых слотов
def get_busy_slots():
    with sqlite3.connect("appointments.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT date, time FROM appointments")
        return {(date, time) for date, time in cursor.fetchall()}


# Функция для добавления записи
def add_appointment(name, phone, date, time, user_id):
    db_path = "appointments.db"

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Проверяем, существует ли уже запись для этого user_id (на любую дату)
        cursor.execute("SELECT COUNT(*) FROM appointments WHERE user_id = ?", (user_id,))
        existing_appointment = cursor.fetchone()[0]

        if existing_appointment > 1:
            return False  # Если запись уже есть, блокируем новую

        # Вставляем новую запись
        cursor.execute("INSERT INTO appointments (user_id, name, phone, date, time) VALUES (?, ?, ?, ?, ?)",
                       (user_id, name, phone, date, time))
        conn.commit()
        return True  # Если запись успешно добавлена


# Функция для создания клавиатуры с доступными датами и временем
def create_available_keyboards():
    busy_slots = get_busy_slots()
    available_dates = []
    available_times_for_dates = {}

    # Определяем сегодняшнюю дату
    today = datetime.now().date()

    # Определяем начальную дату как 1 апреля текущего года
    start_date = datetime(today.year, 4, 1).date()

    # Если 1 апреля уже прошло, начинаем с сегодняшнего дня
    if today > start_date:
        start_date = today

    # Генерируем даты на два месяца вперед, начиная с 1 апреля
    for i in range(60):  # 60 дней должно охватить два месяца
        date = (start_date + timedelta(days=i)).strftime("%d-%m-%Y")
        day_of_week = (start_date + timedelta(days=i)).weekday()

        if day_of_week == 2 or day_of_week == 6:
            continue

        available_times = []
        for hour in range(9, 18, 2):
            time = f"{hour:02}:00"
            if (date, time) not in busy_slots:
                available_times.append(time)

        if available_times:
            available_dates.append(date)
            available_times_for_dates[date] = available_times

    return available_dates, available_times_for_dates



