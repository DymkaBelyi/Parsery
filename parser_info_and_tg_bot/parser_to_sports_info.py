import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
import logging
import os
from dotenv import load_dotenv

import Pars.Parsery.parser_info_and_tg_bot.keyboards as kb


load_dotenv()
TOKEN = os.getenv("TOKEN")

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
    await update.message.reply_text("Выбери категорию:", reply_markup=kb.sports_category)


# Функция обработки сообщений (поиск новостей)
async def handle_button(update: Update, context):
    query = update.callback_query
    news = get_news(query.data)

    await query.answer()
    await query.message.reply_text(news, parse_mode="HTML", disable_web_page_preview=True, reply_markup=kb.sports_category)


# Главная функция
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))  # Команда /start
    app.add_handler(CallbackQueryHandler(handle_button))  # Обработка сообщений

    print("Бот запущен...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
