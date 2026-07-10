from fastapi import APIRouter, HTTPException

from app.core.chroma_client import chroma
from app.core.rag_engine import record_feedback
from app.models.query import FeedbackRequest

router = APIRouter()


@router.post("/api/v1/feedback")
async def feedback(req: FeedbackRequest):
    if req.decision not in ("approve", "disapprove"):
        raise HTTPException(
            status_code=422, detail="decision must be 'approve' or 'disapprove'"
        )
    if req.decision == "disapprove" and not req.reason.strip():
        raise HTTPException(
            status_code=422, detail="reason is required when disapproving"
        )
    return await record_feedback(
        alert_id=req.alert_id,
        analysis=req.analysis,
        decision=req.decision,
        reason=req.reason,
    )


@router.get("/api/v1/feedback")
async def list_feedback():
    col = chroma.get_collection("feedback")
    res = col.get()
    items = []
    if res["ids"]:
        for i, fid in enumerate(res["ids"]):
            meta = res["metadatas"][i] if res["metadatas"] else {}
            doc = res["documents"][i] if res["documents"] else ""
            items.append(
                {
                    "id": fid,
                    "decision": meta.get("decision", ""),
                    "alert_id": meta.get("alert_id", ""),
                    "title": meta.get("title", ""),
                    "created_datetime": meta.get("created_datetime", ""),
                    "text": doc,
                }
            )
    return {"feedback": items, "total": len(items)}
