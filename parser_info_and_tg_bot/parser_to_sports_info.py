import requests
from bs4 import BeautifulSoup
import time
from telegram import Bot
from telegram import Update
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import logging

# Ваши данные
TOKEN = "7550846359:AAFzgkDkvjmrU2kU75lpNNXWtJlg3qSgS28"

# Логирование (чтобы видеть ошибки)
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)


# Функция парсинга новостей
def get_news(category):
    url = f"https://news.sportbox.ru/Vidy_sporta/{category}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    news_items = soup.find("ul", class_="list").find_all("li", limit=5)  # Берём только 5 новостей
    news_list = []

    for item in news_items:
        link = f"https://news.sportbox.ru{item.find('a')['href']}"
        title = item.find('a', class_='title').text.strip()
        news_list.append(f"🔹 <b>{title}</b>\n🔗 {link}")

    return "\n\n".join(news_list) if news_list else "Новости не найдены 😢"


# Функция старта бота
async def start(update: Update, context):
    keyboard = [
        [
            InlineKeyboardButton("Футбол", callback_data="futbol"),
            InlineKeyboardButton("Хоккей", callback_data="hokkej"),
        ],
        [
            InlineKeyboardButton("Бокс", callback_data="boks"),
            InlineKeyboardButton("Теннис", callback_data="tennis"),
        ],
        [
            InlineKeyboardButton("Единоборства", callback_data="edinoborstva"),
            InlineKeyboardButton("Кикбоксинг", callback_data="kickboxing"),
        ],
        [
            InlineKeyboardButton("Биатлон", callback_data="biatlon"),
            InlineKeyboardButton("Баскетбол", callback_data="basketbol"),
        ],
        [
            InlineKeyboardButton("Легкая атлетика", callback_data="light_attletics"),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет! Напиши мне название категории спорта, и я найду свежие новости 🏆",
        reply_markup=reply_markup
    )


# Функция обработки сообщений (поиск новостей)
async def handle_message(update: Update, context):
    query = update.callback_query
    category = query.data  # Получаем категорию спорта из callback_data

    news = get_news(category)  # Парсим новости
    # Отправляем пользователю новости
    await query.answer()  # Оповещаем Telegram, что запрос обработан
    await query.edit_message_text(text=news, parse_mode="HTML", disable_web_page_preview=True)


# Главная функция
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))  # Команда /start
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))  # Обработка сообщений

    print("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
