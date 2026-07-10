from fastapi import APIRouter, HTTPException

from app.core.rag_engine import load_alert_from_store, summarize_alert
from app.models.query import SummarizeRequest

router = APIRouter()


@router.post("/api/v1/summarize")
async def summarize(req: SummarizeRequest):
    if not req.alert_ids:
        raise HTTPException(status_code=422, detail="No alert IDs provided")

    results = []
    for alert_id in req.alert_ids:
        try:
            alert = load_alert_from_store(alert_id)
            if alert is None:
                results.append(
                    {
                        "alert_id": alert_id,
                        "error": "Alert not found in database",
                    }
                )
                continue

            result = await summarize_alert(alert, fmt=req.format)
            results.append(result)
        except Exception as e:
            results.append({"alert_id": alert_id, "error": str(e)})

    return {"summaries": results}
