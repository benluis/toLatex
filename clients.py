# external
import httpx
from openai import AsyncOpenAI
from contextlib import asynccontextmanager

# internal
from models import Setting

http_client = None
openai_client = None


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