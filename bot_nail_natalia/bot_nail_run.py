import os
from dotenv import load_dotenv
import asyncio
from aiogram import Bot, Dispatcher

from other_function import send_reminders, delete_old_appointments
from handlers import router
from admin_handlers import admin_router


# Основной запуск бота
async def main():
    load_dotenv()
    bot = Bot(os.getenv("TOKEN_AUTO"))
    dp = Dispatcher()
    dp.include_routers(router, admin_router)

    # Запуск фонового процесса для отправки напоминаний
    asyncio.create_task(send_reminders())

    # Фоновая задача удаления старых записей
    asyncio.create_task(delete_old_appointments())
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
