from fastapi import APIRouter, HTTPException, Query

from app.core.chroma_client import chroma

router = APIRouter()


@router.get("/api/v1/alerts")
async def list_alerts(
    category: str | None = Query(None),
    severity: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    col = chroma.get_collection("alerts")
    where = {}
    if category:
        where["category"] = category
    if severity:
        where["severity"] = severity
    if status:
        where["status"] = status

    where_clause = where if where else None
    try:
        res = col.get(where=where_clause, limit=limit, offset=offset)
    except Exception:
        res = col.get(limit=limit, offset=offset)

    total = len(res["ids"]) if res["ids"] else 0
    alerts_list = []
    if res["ids"]:
        for i, doc_id in enumerate(res["ids"]):
            meta = res["metadatas"][i] if res["metadatas"] else {}
            alerts_list.append(
                {
                    "id": meta.get("alert_id", doc_id),
                    "title": meta.get("title", ""),
                    "category": meta.get("category", ""),
                    "severity": meta.get("severity", ""),
                    "status": meta.get("status", ""),
                    "created_datetime": meta.get("created_datetime", ""),
                }
            )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "alerts": alerts_list,
    }


@router.get("/api/v1/alerts/{alert_id}")
async def get_alert(alert_id: str):
    col = chroma.get_collection("alerts")
    res = col.get(where={"alert_id": alert_id})
    if not res["ids"]:
        raise HTTPException(status_code=404, detail="Alert not found")

    meta = res["metadatas"][0] if res["metadatas"] else {}
    doc = res["documents"][0] if res["documents"] else ""

    ev_col = chroma.get_collection("evidence")
    ev_res = ev_col.get(where={"alert_id": alert_id})
    evidence_list = []
    if ev_res["ids"]:
        for i, _ in enumerate(ev_res["ids"]):
            ev_meta = ev_res["metadatas"][i] if ev_res["metadatas"] else {}
            ev_doc = ev_res["documents"][i] if ev_res["documents"] else ""
            evidence_list.append(
                {"metadata": ev_meta, "text": ev_doc[:300]}
            )

    return {
        "id": alert_id,
        "metadata": meta,
        "summary": doc[:500] if doc else "",
        "evidence_count": len(evidence_list),
        "evidence": evidence_list,
    }


@router.delete("/api/v1/alerts/{alert_id}")
async def delete_alert(alert_id: str):
    col = chroma.get_collection("alerts")
    res = col.get(where={"alert_id": alert_id})
    if not res["ids"]:
        raise HTTPException(status_code=404, detail="Alert not found")

    ids_to_delete = res["ids"]
    col.delete(ids=ids_to_delete)

    ev_col = chroma.get_collection("evidence")
    ev_res = ev_col.get(where={"alert_id": alert_id})
    if ev_res["ids"]:
        ev_col.delete(ids=ev_res["ids"])

    return {"deleted": True, "alert_id": alert_id, "chunks_removed": len(ids_to_delete)}
