from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


# Создаём reply-клавиатуру с кнопками администратора
admin_kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📜 Посмотреть все записи")],
        [KeyboardButton(text="📝 Записать на маникюр")],
        [KeyboardButton(text="❌ Удалить запись")],
    ],
    resize_keyboard=True
)


# Создаём reply-клавиатуру для пользователей
user_kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="💅 Записаться на маникюр")],
        [KeyboardButton(text="❌ Отменить запись")]
    ],
    resize_keyboard=True,
)


cancel_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Прекратить запись")]],
    resize_keyboard=True,
)

cancel_keyboard_admin = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Отмена записи")]],
    resize_keyboard=True,
)
