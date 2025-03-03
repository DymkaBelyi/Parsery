import os
from dotenv import load_dotenv

import asyncio
from aiogram import Bot, Dispatcher, Router

from other_function import send_reminders, delete_old_appointments
from handlers import router


# Основной запуск бота
async def main():
    load_dotenv()
    bot = Bot(os.getenv("TOKEN_NAIL"))
    dp = Dispatcher()
    dp.include_router(router)

    # Запуск фонового процесса для отправки напоминаний
    asyncio.create_task(send_reminders())

    # Фоновая задача удаления старых записей
    asyncio.create_task(delete_old_appointments())
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
