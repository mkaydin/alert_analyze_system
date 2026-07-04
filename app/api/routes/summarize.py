from fastapi import APIRouter, HTTPException

from app.core.chroma_client import chroma
from app.core.rag_engine import summarize_alert
from app.ingestion.parser import parse_alert_data
from app.models.query import SummarizeRequest

router = APIRouter()


@router.post("/api/v1/summarize")
async def summarize(req: SummarizeRequest):
    if not req.alert_ids:
        raise HTTPException(status_code=422, detail="No alert IDs provided")

    results = []
    for alert_id in req.alert_ids:
        try:
            col = chroma.get_collection("alerts")
            res = col.get(where={"alert_id": alert_id})
            if not res["ids"]:
                results.append(
                    {
                        "alert_id": alert_id,
                        "error": "Alert not found in database",
                    }
                )
                continue

            metadata = res["metadatas"][0] if res["metadatas"] else {}
            doc_text = res["documents"][0] if res["documents"] else ""

            from app.models.alert import Alert, AlertEvidence

            alert = Alert(
                id=alert_id,
                title=metadata.get("title", metadata.get("alert_id", alert_id)),
                description=doc_text,
                category=metadata.get("category", ""),
                severity=metadata.get("severity", ""),
                status=metadata.get("status", ""),
                detection_source=metadata.get("detection_source", ""),
                created_datetime=metadata.get("created_datetime", ""),
                evidence=[],
            )

            result = await summarize_alert(alert, fmt=req.format)
            results.append(result)
        except Exception as e:
            results.append({"alert_id": alert_id, "error": str(e)})

    return {"summaries": results}
