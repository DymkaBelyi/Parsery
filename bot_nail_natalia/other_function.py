from datetime import datetime, timedelta
import sqlite3
import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot


load_dotenv()
bot = Bot(os.getenv("TOKEN_NAIL"))
ADMIN_IDS = [int(admin_id) for admin_id in os.getenv("ADMINS_NAIL", "Ба").split(",")]


# Функция отправки напоминаний
async def send_reminders():
    conn = sqlite3.connect("appointments.db")
    cursor = conn.cursor()

    while True:
        try:
            now = datetime.now()
            target_time = now.replace(hour=10, minute=0, second=0, microsecond=0)  # 10:00 утра

            if now > target_time:
                target_time += timedelta(days=1)  # Если время уже прошло, ждем до следующего дня

            wait_time = (target_time - now).total_seconds()
            await asyncio.sleep(wait_time)  # Ждём до 10:00

            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%d-%m-%Y")
            cursor.execute("SELECT user_id, name, phone, date, time FROM appointments WHERE date = ? "
                           "ORDER BY time ASC", (tomorrow,))
            appointments = cursor.fetchall()

            if appointments:
                for user_id, name, phone, date, time in appointments:
                    message = (
                        f"🔔 Напоминание!\n"
                        f"💅 Завтра у вас запись на маникюр!\n"
                        f"📅 Дата: {date}\n"
                        f"⏰ Время: {time}\n"
                        f"Ждём вас! 😊"
                    )
                    try:
                        await bot.send_message(user_id, message)
                    except Exception as e:
                        print(f"Ошибка отправки клиенту {user_id}: {e}")

                admin_message = "📋 Записи на завтра:\n\n"
                admin_message += "\n\n".join([
                    f"👤 {name}\n📞 {phone}\n⏰ {time}" for _, name, phone, _, time in appointments
                ])

                for admin_id in ADMIN_IDS:
                    try:
                        await bot.send_message(admin_id, f"\n{admin_message}")
                    except Exception as e:
                        print(f"Ошибка отправки админу {admin_id}: {e}")

        except Exception as e:
            print(f"Ошибка в send_reminders: {e}")
            await asyncio.sleep(3600)  # Если ошибка, ждем час и пробуем снова


# Функция удаления устаревших записей
async def delete_old_appointments():
    conn = sqlite3.connect("appointments.db")
    cursor = conn.cursor()
    while True:
        try:
            today = datetime.now().strftime("%d-%m-%Y")

            # Удаляем записи, у которых дата меньше текущей
            cursor.execute("DELETE FROM appointments WHERE date < ?", (today,))
            conn.commit()

            # Ждем до следующего дня в 00:00
            now = datetime.now()
            next_run = datetime.combine(now.date() + timedelta(days=1), datetime.min.time())
            sleep_seconds = (next_run - now).total_seconds()

            # Ждём до следующего дня (раз в сутки)
            await asyncio.sleep(sleep_seconds)  # 24 часа

        except Exception as e:
            print(f"Ошибка в delete_old_appointments: {e}")
            await asyncio.sleep(3600)  # Если ошибка, ждем час и пробуем снова


