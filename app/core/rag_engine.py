import time

import httpx

from app.config import settings
from app.core.chroma_client import chroma
from app.core.embeddings import embed_client
from app.core.llm_client import llm_client
from app.core.prompts import (
    ANALYZE_PROMPT,
    CATEGORIZE_PROMPT,
    QUERY_PROMPT,
    SUMMARIZE_PROMPT,
)
from app.models.alert import Alert


async def query_rag(
    query: str,
    num_results: int = 5,
    filters: dict | None = None,
    model: str | None = None,
) -> dict:
    start = time.time()

    query_embedding = await embed_client.embed_one(query)

    where_filter = None
    if filters:
        where_filter = {k: v for k, v in filters.items() if v}

    results = {}
    for collection_name in ("alerts", "evidence", "documents", "rules", "flags"):
        col = chroma.get_collection(collection_name)
        try:
            res = col.query(
                query_embeddings=[query_embedding],
                n_results=num_results,
                where=where_filter,
            )
            if res["ids"] and res["ids"][0]:
                results[collection_name] = res
        except Exception:
            pass

    retrieved_chunks = []
    for coll_name, res in results.items():
        for i, doc_id in enumerate(res["ids"][0]):
            retrieved_chunks.append(
                {
                    "id": doc_id,
                    "text": res["documents"][0][i],
                    "metadata": res["metadatas"][0][i],
                    "collection": coll_name,
                    "relevance": res["distances"][0][i] if res.get("distances") else 0,
                }
            )

    if not retrieved_chunks:
        return {
            "answer": "No relevant alerts found. Try broadening your query.",
            "sources": [],
            "processing_time_ms": int((time.time() - start) * 1000),
        }

    context_text = "\n\n".join(
        f"[{c['collection']}] {c['text']}" for c in retrieved_chunks
    )

    prompt = QUERY_PROMPT.format(retrieved_chunks=context_text, query=query)

    answer = await llm_client.generate(prompt)

    sources = [
        {
            "chunk_id": c["id"],
            "alert_id": c["metadata"].get("alert_id", ""),
            "type": c["metadata"].get("type", ""),
            "relevance": round(1 - c["relevance"], 4) if c["relevance"] else 0,
        }
        for c in retrieved_chunks[:num_results]
    ]

    return {
        "answer": answer,
        "sources": sources,
        "processing_time_ms": int((time.time() - start) * 1000),
    }


async def summarize_alert(alert: Alert, fmt: str = "concise") -> dict:
    evidence_lines = []
    for ev in alert.evidence:
        odata = ev.odata_type.split(".")[-1] if "." in ev.odata_type else ev.odata_type
        detail_preview = str(ev.details)[:200]
        evidence_lines.append(f"- [{odata}] verdict={ev.verdict} {detail_preview}")

    evidence_text = "\n".join(evidence_lines) if evidence_lines else "No evidence"

    prompt = SUMMARIZE_PROMPT.format(
        title=alert.title,
        category=alert.category,
        severity=alert.severity,
        description=alert.description,
        detection_source=alert.detection_source,
        status=alert.status,
        evidence_text=evidence_text,
    )

    if fmt == "concise":
        prompt += "\n\nBe concise — 3-5 bullet points max."
    elif fmt == "soc-report":
        prompt += "\n\nProduce a full SOC report format with sections."
    elif fmt == "detailed":
        prompt += "\n\nProvide a detailed technical analysis."

    answer = await llm_client.generate(prompt)
    return {"alert_id": alert.id, "summary": answer, "format": fmt}


async def analyze_alert(
    alert: Alert, include_similar: bool = True
) -> dict:
    alert_summary = (
        f"Title: {alert.title}\n"
        f"Category: {alert.category}\n"
        f"Severity: {alert.severity}\n"
        f"Description: {alert.description}\n"
        f"Detection: {alert.detection_source}\n"
        f"Status: {alert.status}\n"
        f"Evidence count: {len(alert.evidence)}"
    )

    similar_context = "No similar historical alerts found."
    similar_sources = []
    if include_similar:
        query_embedding = await embed_client.embed_one(alert.description)
        col = chroma.get_collection("alerts")
        try:
            res = col.query(
                query_embeddings=[query_embedding],
                n_results=5,
                where={"alert_id": {"$ne": alert.id}},
            )
            if res["ids"] and res["ids"][0]:
                similar_parts = []
                for i, doc_id in enumerate(res["ids"][0]):
                    meta = res["metadatas"][0][i]
                    doc_text = res["documents"][0][i]
                    similar_parts.append(
                        f"--- Similar Alert ---\n"
                        f"Alert ID: {meta.get('alert_id', '')}\n"
                        f"Content: {doc_text[:300]}"
                    )
                    similar_sources.append(
                        {
                            "alert_id": meta.get("alert_id", ""),
                            "type": meta.get("type", ""),
                            "relevance": round(1 - res["distances"][0][i], 4)
                            if res.get("distances")
                            else 0,
                        }
                    )
                similar_context = "\n\n".join(similar_parts)
        except Exception:
            pass

    prompt = ANALYZE_PROMPT.format(
        alert_summary=alert_summary,
        similar_alerts_context=similar_context,
    )

    answer = await llm_client.generate(prompt)
    return {
        "alert_id": alert.id,
        "analysis": answer,
        "similar_alerts": similar_sources,
    }


async def categorize_alert(alert: Alert) -> dict:
    evidence_lines = []
    for ev in alert.evidence:
        odata = ev.odata_type.split(".")[-1] if "." in ev.odata_type else ev.odata_type
        evidence_lines.append(f"- [{odata}] {str(ev.details)[:150]}")
    evidence_text = "\n".join(evidence_lines) if evidence_lines else "No evidence"

    prompt = CATEGORIZE_PROMPT.format(
        title=alert.title,
        description=alert.description,
        evidence_text=evidence_text,
    )

    category = await llm_client.generate(prompt)
    return {"alert_id": alert.id, "category_assignment": category}
