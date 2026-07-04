import asyncio

import httpx

from app.config import settings


class OllamaLLMClient:
    def __init__(self):
        self.semaphore = asyncio.Semaphore(settings.ollama_concurrency)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=settings.ollama_timeout)
        return self._client

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        client = await self._get_client()
        async with self.semaphore:
            resp = await client.post(
                f"{settings.ollama_host}/api/generate",
                json={
                    "model": settings.llm_model,
                    "prompt": prompt,
                    "system": system_prompt,
                    "stream": False,
                    "options": {
                        "temperature": settings.llm_temperature,
                        "num_predict": settings.llm_max_tokens,
                    },
                },
            )
            resp.raise_for_status()
            data = resp.json()
        return data["response"]

    async def close(self):
        if self._client:
            await self._client.aclose()


llm_client = OllamaLLMClient()
