import time

import httpx
from fastapi import APIRouter

from app.config import settings
from app.core.chroma_client import chroma

router = APIRouter()

_start_time: float = time.time()


@router.get("/api/v1/health")
async def health():
    ollama_reachable = False
    ollama_models = []

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{settings.ollama_host}/api/tags")
            if resp.status_code == 200:
                ollama_reachable = True
                data = resp.json()
                ollama_models = [m["name"] for m in data.get("models", [])]
    except Exception:
        pass

    chroma_ok = chroma.heartbeat()
    collections = chroma.list_collections()
    total_docs = 0
    coll_info = []
    for c in collections:
        cnt = c.count()
        total_docs += cnt
        coll_info.append({"name": c.name, "documents": cnt})

    uptime = time.time() - _start_time

    return {
        "status": "healthy" if (ollama_reachable and chroma_ok) else "degraded",
        "uptime_seconds": round(uptime),
        "ollama": {
            "reachable": ollama_reachable,
            "models": ollama_models,
            "concurrency": {"active": 0, "max": settings.ollama_concurrency, "queue": 0},
        },
        "chromadb": {
            "status": "connected" if chroma_ok else "disconnected",
            "collections": coll_info,
            "documents": total_docs,
        },
    }


@router.get("/api/v1/stats")
async def stats():
    collections = chroma.list_collections()
    result = {}
    for c in collections:
        result[c.name] = c.count()
    return {"collections": result}
