import json
import re
import time
import uuid
from datetime import datetime, timezone

from app.core.chroma_client import chroma
from app.core.embeddings import embed_client
from app.core.llm_client import llm_client
from app.core.prompts import (
    ANALYZE_PROMPT,
    CATEGORIZE_PROMPT,
    FEEDBACK_PROMPT,
    QUERY_PROMPT,
    SUMMARIZE_PROMPT,
    SYSTEM_GUARDRAIL,
)
from app.ingestion.ingestor import ingest_alerts
from app.ingestion.parser import parse_alert_data
from app.models.alert import Alert, AlertEvidence

_AGENTIC_LINE = re.compile(
    r"^\s*(let me\b|i'?ll\b|i will\b|first,? let|let's\b|now let)", re.IGNORECASE
)
_COMMAND_LINE = re.compile(
    r"^\s*(\$|#\s|cat\s|ls\s|grep\s|cd\s|head\s|tail\s|less\s|more\s|open\s)",
    re.IGNORECASE,
)
_FILE_URL_LINE = re.compile(
    r"^\s*(file://\S+|/[\w./-]+\.(?:json|txt|md|log))\s*$", re.IGNORECASE
)


def _sanitize(text: str) -> str:
    """Strip agentic preamble / shell commands / bare file paths a model may emit."""
    if not text:
        return text
    lines = text.splitlines()
    cleaned: list[str] = []
    for line in lines:
        if _AGENTIC_LINE.match(line) or _COMMAND_LINE.match(line) or _FILE_URL_LINE.match(line):
            continue
        cleaned.append(line)
    result = "\n".join(cleaned).strip()
    return result or text.strip()


async def _generate(prompt: str) -> str:
    return _sanitize(await llm_client.generate(prompt, system_prompt=SYSTEM_GUARDRAIL))


def load_alert_from_store(alert_id: str) -> Alert | None:
    col = chroma.get_collection("alerts")
    res = col.get(where={"alert_id": alert_id})
    if not res["ids"]:
        return None

    meta = res["metadatas"][0] if res["metadatas"] else {}
    doc = res["documents"][0] if res["documents"] else ""

    ev_col = chroma.get_collection("evidence")
    ev_res = ev_col.get(where={"alert_id": alert_id})
    evidence = []
    if ev_res["ids"]:
        for i, _ in enumerate(ev_res["ids"]):
            ev_meta = ev_res["metadatas"][i] if ev_res["metadatas"] else {}
            ev_doc = ev_res["documents"][i] if ev_res["documents"] else ""
            details = dict(ev_meta)
            details["text"] = ev_doc
            evidence.append(
                AlertEvidence(
                    odata_type=ev_meta.get("odata_type", ev_meta.get("type", "")),
                    verdict=ev_meta.get("verdict"),
                    details=details,
                )
            )

    return Alert(
        id=alert_id,
        title=meta.get("title", ""),
        description=doc,
        category=meta.get("category", ""),
        severity=meta.get("severity", ""),
        status=meta.get("status", ""),
        detection_source=meta.get("detection_source", ""),
        created_datetime=meta.get("created_datetime") or None,
        evidence=evidence,
    )


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
    for collection_name in ("alerts", "evidence", "documents", "rules", "flags", "feedback"):
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

    answer = await _generate(prompt)

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

    answer = await _generate(prompt)
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

    answer = await _generate(prompt)
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

    category = await _generate(prompt)
    return {"alert_id": alert.id, "category_assignment": category}


def _synthetic_alert(text: str) -> Alert:
    stripped = text.strip()
    first_line = stripped.splitlines()[0].strip() if stripped else ""
    title = (first_line[:120] or "Pasted alert text")
    return Alert(
        id=f"text_{uuid.uuid4().hex[:16]}",
        title=title,
        description=stripped,
        category="",
        severity="",
        status="new",
        detection_source="manual-input",
        created_datetime=datetime.now(timezone.utc),
        evidence=[],
    )


async def analyze_input(content: str, content_type: str = "auto") -> dict:
    content = (content or "").strip()
    if not content:
        raise ValueError("Content is empty")

    data = None
    if content_type in ("auto", "json"):
        try:
            data = json.loads(content)
        except (json.JSONDecodeError, ValueError):
            if content_type == "json":
                raise ValueError("Content is not valid JSON")
            data = None

    if data is not None and isinstance(data, (dict, list)):
        alerts = parse_alert_data(data)
        if not alerts:
            raise ValueError("No alerts found in JSON payload")
        await ingest_alerts(alerts)
        primary = alerts[0]
        input_type = "json"
    else:
        primary = _synthetic_alert(content)
        await ingest_alerts([primary])
        input_type = "text"

    analysis = await analyze_alert(primary, include_similar=True)
    summary = await summarize_alert(primary, fmt="concise")

    return {
        "alert_id": primary.id,
        "input_type": input_type,
        "title": primary.title,
        "analysis": analysis["analysis"],
        "summary": summary["summary"],
        "similar_alerts": analysis.get("similar_alerts", []),
    }


async def record_feedback(
    alert_id: str,
    analysis: str,
    decision: str,
    reason: str = "",
) -> dict:
    alert = load_alert_from_store(alert_id)
    alert_context = (
        f"Title: {alert.title}\nCategory: {alert.category}\n"
        f"Severity: {alert.severity}\nDescription: {alert.description}"
        if alert
        else f"Alert ID: {alert_id} (details not found in store)"
    )

    if decision == "disapprove":
        prompt = FEEDBACK_PROMPT.format(
            alert=alert_context,
            analysis=analysis or "(not provided)",
            reason=reason,
        )
        knowledge = await _generate(prompt)
    else:
        knowledge = (
            f"Analyst APPROVED the automated analysis for alert '{alert.title}'."
            if alert
            else f"Analyst APPROVED the automated analysis for alert {alert_id}."
        )

    document = (
        f"Feedback ({decision}) for alert {alert_id}\n"
        f"Alert: {alert.title if alert else alert_id}\n"
        f"Analyst reason: {reason or 'N/A'}\n"
        f"Knowledge: {knowledge}"
    )

    embedding = await embed_client.embed([document])
    knowledge_id = f"fb_{uuid.uuid4().hex[:16]}"
    col = chroma.get_collection("feedback")
    col.add(
        ids=[knowledge_id],
        embeddings=embedding,
        metadatas=[
            {
                "type": "feedback",
                "decision": decision,
                "alert_id": alert_id,
                "title": alert.title if alert else "",
                "created_datetime": datetime.now(timezone.utc).isoformat(),
            }
        ],
        documents=[document],
    )

    return {
        "stored": True,
        "knowledge_id": knowledge_id,
        "decision": decision,
        "knowledge": knowledge,
    }
