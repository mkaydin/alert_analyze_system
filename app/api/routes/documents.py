import os
import tempfile
import uuid

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from app.config import settings
from app.core.chroma_client import chroma
from app.core.embeddings import embed_client
from app.ingestion.document_loader import (
    ingest_document_file,
    ingest_directory,
    load_all_reference_documents,
)

router = APIRouter()


class IngestDocumentItem(BaseModel):
    text: str
    metadata: dict = {}


class IngestDocumentBatch(BaseModel):
    documents: list[IngestDocumentItem]
    collection: str = "documents"


@router.post("/api/v1/ingest-document")
async def ingest_document_text(payload: IngestDocumentBatch):
    col = chroma.get_collection(payload.collection)
    batch_size = settings.ollama_concurrency * 2
    results = {"ingested": 0, "errors": 0}
    for i in range(0, len(payload.documents), batch_size):
        batch = payload.documents[i : i + batch_size]
        texts = [d.text for d in batch]
        embeddings = await embed_client.embed(texts)
        ids = [str(uuid.uuid4()) for _ in batch]
        metadatas = [d.metadata for d in batch]
        col.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=texts)
        results["ingested"] += len(batch)
    return results


@router.post("/api/v1/documents/ingest-file")
async def ingest_document(file: UploadFile = File(...)):
    if not file.filename.endswith(".md"):
        raise HTTPException(
            status_code=422, detail="Only .md files are supported"
        )

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".md")
    try:
        content = await file.read()
        tmp.write(content)
        tmp.close()
        result = await ingest_document_file(tmp.name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.unlink(tmp.name)

    return result


@router.post("/api/v1/documents/ingest-directory")
async def ingest_documents_from_path(payload: dict):
    path = payload.get("path", "")
    if not path or not os.path.isdir(path):
        raise HTTPException(status_code=422, detail="Valid directory path required")

    try:
        results = await ingest_directory(path)
        return {"results": results, "total": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/v1/documents/load-reference")
async def load_reference():
    try:
        results = await load_all_reference_documents()
        total = sum(r.get("chunks_created", 0) for r in results)
        return {"results": results, "total_chunks": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/documents")
async def list_documents():
    try:
        col = chroma.get_collection("documents")
        res = col.get()
        docs = []
        seen = set()
        if res["ids"]:
            for i, _ in enumerate(res["ids"]):
                meta = res["metadatas"][i] if res["metadatas"] else {}
                key = (meta.get("title", ""), meta.get("source", ""))
                if key not in seen:
                    seen.add(key)
                    docs.append(
                        {
                            "title": meta.get("title", ""),
                            "source": meta.get("source", ""),
                            "chunks": sum(
                                1
                                for m in (res["metadatas"] or [])
                                if m.get("title") == meta.get("title")
                            ),
                        }
                    )
        all_docs = list(seen)
        return {"documents": [{"title": t, "source": s} for t, s in seen]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/v1/documents")
async def clear_documents():
    try:
        col = chroma.get_collection("documents")
        res = col.get()
        if res["ids"]:
            col.delete(ids=res["ids"])
        return {"deleted": True, "count": len(res["ids"])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
