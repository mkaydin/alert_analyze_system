from app.config import settings
from app.core.chroma_client import chroma
from app.core.embeddings import embed_client
from app.ingestion.chunker import Chunk, chunk_alert


async def ingest_alerts(alerts: list) -> dict:
    all_chunks: list[Chunk] = []
    alert_ids = set()

    for alert in alerts:
        alert_ids.add(alert.id)
        all_chunks.extend(chunk_alert(alert))

    if not all_chunks:
        return {"ingested": len(alerts), "chunks_created": 0, "alert_ids": list(alert_ids)}

    by_collection: dict[str, list[Chunk]] = {}
    for c in all_chunks:
        by_collection.setdefault(c.collection, []).append(c)

    batch_size = settings.ollama_concurrency * 2

    for collection_name, chunks in by_collection.items():
        col = chroma.get_collection(collection_name)

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            texts = [c.text for c in batch]
            embeddings = await embed_client.embed(texts)
            col.add(
                ids=[c.id for c in batch],
                embeddings=embeddings,
                metadatas=[c.metadata for c in batch],
                documents=[c.text for c in batch],
            )

    return {
        "ingested": len(alerts),
        "chunks_created": len(all_chunks),
        "alert_ids": list(alert_ids),
    }
