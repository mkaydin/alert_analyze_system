from fastapi import APIRouter, HTTPException

from app.core.rag_engine import (
    analyze_alert,
    analyze_input,
    categorize_alert,
    load_alert_from_store,
)
from app.models.query import AnalyzeInputRequest, AnalyzeRequest

router = APIRouter()


@router.post("/api/v1/analyze-input")
async def analyze_input_route(req: AnalyzeInputRequest):
    try:
        return await analyze_input(req.content, req.content_type)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


def _build_alert_from_chroma(alert_id: str):
    alert = load_alert_from_store(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    return alert


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
