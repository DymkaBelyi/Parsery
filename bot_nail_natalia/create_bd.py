import sqlite3
from datetime import datetime, timedelta

MAX_SLOTS_PER_DAY = 5

# Инициализация базы данных
def init_db():
    with sqlite3.connect("appointments.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS appointments
                          (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id, name TEXT, phone TEXT, date TEXT, time TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS schedule
                          (date TEXT PRIMARY KEY, max_slots INTEGER)''')
        conn.commit()


# Функция для добавления дат в расписание
def add_schedule_dates():
    with sqlite3.connect("appointments.db") as conn:
        cursor = conn.cursor()
        for i in range(30):
            date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
            cursor.execute("INSERT OR IGNORE INTO schedule (date, max_slots) VALUES (?, ?)", (date, MAX_SLOTS_PER_DAY))
        conn.commit()

init_db()
add_schedule_dates()


# Функция для получения занятых слотов
def get_busy_slots():
    with sqlite3.connect("appointments.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT date, time FROM appointments")
        return {(date, time) for date, time in cursor.fetchall()}


# Функция для добавления записи
def add_appointment(name, phone, date, time, user_id):
    with sqlite3.connect("appointments.db") as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO appointments (name, phone, date, time, user_id) VALUES (?, ?, ?, ?, ?)",
                       (name, phone, date, time, user_id))
        conn.commit()


# Функция для создания клавиатуры с доступными датами и временем
def create_available_keyboards():
    busy_slots = get_busy_slots()

    # Создаем список доступных дат и времени
    available_dates = []
    available_times_for_dates = {}

    # Генерируем даты на месяц вперед
    for i in range(30):
        date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
        day_of_week = (datetime.now() + timedelta(days=i)).weekday()  # Получаем день недели (0 - понедельник, 6 - воскресенье)

        # Исключаем среду (2) и воскресенье (6)
        if day_of_week == 2 or day_of_week == 6:
            continue

        # Проверяем наличие свободного времени для этой даты
        available_times = []
        for hour in range(9, 18, 2):  # Интервал в 2 часа от 9:00 до 17:00
            time = f"{hour:02}:00"
            if (date, time) not in busy_slots:
                available_times.append(time)

        # Добавляем дату в available_dates только если есть свободное время
        if available_times:
            available_dates.append(date)
            available_times_for_dates[date] = available_times

    return available_dates, available_times_for_dates
