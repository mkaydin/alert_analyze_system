from fastapi import APIRouter, HTTPException

from app.core.chroma_client import chroma
from app.core.rag_engine import analyze_alert, categorize_alert
from app.models.query import AnalyzeRequest
from app.models.alert import Alert, AlertEvidence
from app.ingestion.parser import parse_alert_data

router = APIRouter()


def _build_alert_from_chroma(alert_id: str) -> Alert:
    col = chroma.get_collection("alerts")
    res = col.get(where={"alert_id": alert_id})
    if not res["ids"]:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

    meta = res["metadatas"][0] if res["metadatas"] else {}
    doc = res["documents"][0] if res["documents"] else ""

    ev_col = chroma.get_collection("evidence")
    ev_res = ev_col.get(where={"alert_id": alert_id})
    evidence = []
    if ev_res["ids"]:
        for i, _ in enumerate(ev_res["ids"]):
            ev_meta = ev_res["metadatas"][i] if ev_res["metadatas"] else {}
            evidence.append(
                AlertEvidence(
                    odata_type=ev_meta.get("odata_type", ev_meta.get("type", "")),
                    verdict=ev_meta.get("verdict"),
                    details=ev_meta,
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
        created_datetime=meta.get("created_datetime", ""),
        evidence=evidence,
    )


@router.post("/api/v1/analyze")
async def analyze(req: AnalyzeRequest):
    alert = _build_alert_from_chroma(req.alert_id)
    result = await analyze_alert(alert, include_similar=req.include_similar)
    return result


@router.post("/api/v1/analyze/categorize")
async def categorize(payload: dict):
    alert_id = payload.get("alert_id", "")
    if not alert_id:
        raise HTTPException(status_code=422, detail="alert_id required")

    alert = _build_alert_from_chroma(alert_id)
    result = await categorize_alert(alert)
    return result
