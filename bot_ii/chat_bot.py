import os

from dotenv import load_dotenv
from openai import AsyncOpenAI
import asyncio
from mistralai import Mistral


async def generate(content):
    load_dotenv()
    async with Mistral(
        api_key=os.getenv("MISTRAL_API_KEY", ""),
    ) as mistral:

        res = await mistral.chat.complete_async(model="mistral-large-latest", messages=[
            {
                "content": content,
                "role": "user",
            },
        ], stream=False)
    if res is not None:
        return res


