from fastapi import APIRouter, HTTPException

from app.core.rag_engine import query_rag
from app.models.query import QueryRequest, QueryResponse

router = APIRouter()


@router.post("/api/v1/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    try:
        result = await query_rag(
            query=req.query,
            num_results=req.num_results,
            filters=req.filters,
            model=req.model,
        )
        return QueryResponse(
            answer=result["answer"],
            sources=result["sources"],
            processing_time_ms=result["processing_time_ms"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
