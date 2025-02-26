from datetime import datetime, timedelta
import sqlite3
import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot

load_dotenv()

TOKEN = os.getenv("TOKEN_NAIL")
bot = Bot(TOKEN)

conn = sqlite3.connect("appointments.db")
cursor = conn.cursor()

ADMIN_IDS = [int(admin_id) for admin_id in os.getenv("ADMINS_NAIL", "Ба").split(",")]


# Функция отправки напоминаний
async def send_reminders():
    while True:
        try:
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

            # Получаем всех клиентов, записанных на завтра
            cursor.execute("SELECT user_id, name, phone, date, time FROM appointments WHERE date = ? "
                           "ORDER BY time ASC", (tomorrow,))
            appointments = cursor.fetchall()

            if appointments:
                # Отправляем клиентам напоминания
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

                # Отправляем администраторам список записанных клиентов с номерами телефонов
                admin_message = "📋 Записи на завтра:\n\n"
                admin_message += "\n\n".join([
                    f"👤 {name}\n📞 {phone}\n⏰ {time}" for _, name, phone, _, time in appointments
                ])

                for admin_id in ADMIN_IDS:
                    try:
                        await bot.send_message(admin_id, f"\n{admin_message}")
                    except Exception as e:
                        print(f"Ошибка отправки админу {admin_id}: {e}")

            # Ждём до следующего дня (раз в сутки)
            await asyncio.sleep(86400)  # 24 часа

        except Exception as e:
            print(f"Ошибка в send_reminders: {e}")
            await asyncio.sleep(3600)  # Если ошибка, ждем час и пробуем снова


# Функция удаления устаревших записей
async def delete_old_appointments():
    while True:
        try:
            today = datetime.now().strftime("%Y-%m-%d")

            # Удаляем записи, у которых дата меньше текущей
            cursor.execute("DELETE FROM appointments WHERE date < ?", (today,))
            conn.commit()

            # Ждём до следующего дня (раз в сутки)
            await asyncio.sleep(86400)  # 24 часа

        except Exception as e:
            print(f"Ошибка в delete_old_appointments: {e}")
            await asyncio.sleep(3600)  # Если ошибка, ждем час и пробуем снова


