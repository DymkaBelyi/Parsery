import os

from dotenv import load_dotenv
from openai import AsyncOpenAI


load_dotenv()
client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)


async def generate(text) -> None:
    chat_completion = await client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": text,
            }
        ],
        model="gpt-4o-mini",
    )

    return chat_completion.choices[0].message.content


