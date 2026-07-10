from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.ingest import router as ingest_router
from app.api.routes.query import router as query_router
from app.api.routes.summarize import router as summarize_router
from app.api.routes.analyze import router as analyze_router
from app.api.routes.alerts import router as alerts_router
from app.api.routes.rules import router as rules_router
from app.api.routes.documents import router as documents_router
from app.api.routes.feedback import router as feedback_router
from app.core.chroma_client import chroma
from app.core.embeddings import embed_client
from app.core.llm_client import llm_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    chroma.initialize()
    yield
    await embed_client.close()
    await llm_client.close()


app = FastAPI(
    title="Alert Analysis RAG System",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(ingest_router)
app.include_router(query_router)
app.include_router(summarize_router)
app.include_router(analyze_router)
app.include_router(alerts_router)
app.include_router(rules_router)
app.include_router(documents_router)
app.include_router(feedback_router)
