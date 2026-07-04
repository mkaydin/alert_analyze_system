from fastapi import APIRouter, HTTPException

from app.ingestion.ingestor import ingest_alerts
from app.ingestion.parser import parse_alert_data

router = APIRouter()


@router.post("/api/v1/ingest")
async def ingest(payload: dict):
    try:
        alerts = parse_alert_data(payload)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse alert data: {e}")

    if not alerts:
        raise HTTPException(status_code=422, detail="No alerts found in payload")

    result = await ingest_alerts(alerts)
    return result


@router.post("/api/v1/ingest/batch")
async def ingest_batch(payload: list[dict]):
    if not payload:
        raise HTTPException(status_code=422, detail="Empty batch payload")

    all_alerts = []
    for item in payload:
        try:
            alerts = parse_alert_data(item)
            all_alerts.extend(alerts)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Failed to parse item: {e}")

    result = await ingest_alerts(all_alerts)
    return result
