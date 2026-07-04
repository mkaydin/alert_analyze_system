from pydantic import BaseModel


class DetectionRule(BaseModel):
    id: str | None = None
    name: str
    description: str = ""
    category: str = ""
    severity: str = "medium"
    mitre_techniques: list[str] = []
    indicators: list[str] = []
    iocs: list[str] = []
