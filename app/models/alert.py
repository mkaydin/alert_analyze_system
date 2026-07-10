from datetime import datetime
from pydantic import BaseModel


class AlertEvidence(BaseModel):
    odata_type: str
    verdict: str | None = None
    remediation_status: str | None = None
    details: dict = {}


class Alert(BaseModel):
    id: str
    incident_id: str | None = None
    title: str
    description: str
    category: str
    severity: str
    status: str
    detection_source: str
    product_name: str = ""
    service_source: str = ""
    created_datetime: datetime | None = None
    first_activity_datetime: datetime | None = None
    last_activity_datetime: datetime | None = None
    mitre_techniques: list[str] = []
    evidence: list[AlertEvidence] = []
    tags: list[str] = []
    comments: list[dict] = []
    alert_web_url: str | None = None


class AlertCollection(BaseModel):
    total_count: int
    alerts: list[Alert]
