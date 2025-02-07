import asyncio

from aiogram import Bot, Dispatcher
import os
from dotenv import load_dotenv
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from chat_bot import generate

load_dotenv()
TG_TOKEN = os.getenv("TG_TOKEN")

dp = Dispatcher()


class Reg(StatesGroup):
    wait = State()


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Добро пожаловать в бот с ИИ")


@dp.message(Reg.wait)
async def waiting(message: Message):
    await message.answer('Подождите, ваш запрос обрабатывается!!!!!')


@dp.message()
async def gpt(message: Message, state: FSMContext):
    await state.set_state(Reg.wait)
    result = await generate(message.text)
    await message.answer(result)
    await state.clear()


async def main():
    bot = Bot(TG_TOKEN)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())