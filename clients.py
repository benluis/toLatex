# built-in
import os
from contextlib import asynccontextmanager

# external
import httpx
from openai import AsyncOpenAI
from dotenv import load_dotenv

# load environment variables from .env file
load_dotenv()

openai_client: AsyncOpenAI = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

http_client = None


@asynccontextmanager
async def lifespan(app):
    global http_client, openai_client

    settings = Setting()

    http_client = httpx.AsyncClient(timeout=30.0)
    openai_client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        http_client=http_client
    )

    yield

    if http_client:
        await http_client.aclose()