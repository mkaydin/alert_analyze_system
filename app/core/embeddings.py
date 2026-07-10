import asyncio

import httpx

from app.config import settings


class OllamaEmbedClient:
    def __init__(self):
        self.semaphore = asyncio.Semaphore(settings.ollama_concurrency)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=settings.ollama_timeout)
        return self._client

    async def embed(self, texts: list[str]) -> list[list[float]]:
        client = await self._get_client()
        async with self.semaphore:
            resp = await client.post(
                f"{settings.ollama_host}/api/embed",
                json={"model": settings.embed_model, "input": texts},
            )
            resp.raise_for_status()
            data = resp.json()
        return data["embeddings"]

    async def embed_one(self, text: str) -> list[float]:
        return (await self.embed([text]))[0]

    def stats(self) -> dict:
        available = self.semaphore._value
        waiters = self.semaphore._waiters
        return {
            "active": settings.ollama_concurrency - available,
            "max": settings.ollama_concurrency,
            "queue": len(waiters) if waiters else 0,
        }

    async def close(self):
        if self._client:
            await self._client.aclose()


embed_client = OllamaEmbedClient()
