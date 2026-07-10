from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str
    num_results: int = 5
    filters: dict[str, str] | None = None
    model: str = "ornith:latest"


class QueryResponse(BaseModel):
    answer: str
    sources: list[dict] = []
    processing_time_ms: int = 0


class SummarizeRequest(BaseModel):
    alert_ids: list[str]
    format: str = "concise"


class AnalyzeRequest(BaseModel):
    alert_id: str
    include_similar: bool = True


class AnalyzeInputRequest(BaseModel):
    content: str
    content_type: str = "auto"


class FeedbackRequest(BaseModel):
    alert_id: str
    analysis: str = ""
    decision: str
    reason: str = ""
