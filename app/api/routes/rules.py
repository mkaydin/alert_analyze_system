import uuid

from fastapi import APIRouter

from app.core.chroma_client import chroma
from app.models.rule import DetectionRule

router = APIRouter()


@router.get("/api/v1/rules")
async def list_rules():
    col = chroma.get_collection("rules")
    res = col.get()
    rules = []
    if res["ids"]:
        for i, doc_id in enumerate(res["ids"]):
            meta = res["metadatas"][i] if res["metadatas"] else {}
            doc = res["documents"][i] if res["documents"] else ""
            rules.append(
                {
                    "id": meta.get("rule_id", doc_id),
                    "name": meta.get("name", ""),
                    "category": meta.get("category", ""),
                    "severity": meta.get("severity", ""),
                    "description": doc,
                    "mitre_techniques": meta.get("mitre_techniques", "").split(",")
                    if meta.get("mitre_techniques")
                    else [],
                }
            )
    return {"rules": rules, "total": len(rules)}


@router.post("/api/v1/rules")
async def create_rule(rule: DetectionRule):
    from app.core.embeddings import embed_client

    rule_id = rule.id or str(uuid.uuid4())
    text = (
        f"Rule: {rule.name}\n"
        f"Description: {rule.description}\n"
        f"Category: {rule.category}\n"
        f"Severity: {rule.severity}\n"
        f"MITRE: {', '.join(rule.mitre_techniques)}\n"
        f"Indicators: {', '.join(rule.indicators)}\n"
        f"IOCs: {', '.join(rule.iocs)}"
    )

    embeddings = await embed_client.embed([text])

    col = chroma.get_collection("rules")
    col.add(
        ids=[rule_id],
        embeddings=embeddings,
        metadatas=[
            {
                "rule_id": rule_id,
                "name": rule.name,
                "category": rule.category,
                "severity": rule.severity,
                "mitre_techniques": ",".join(rule.mitre_techniques),
            }
        ],
        documents=[text],
    )

    return {"id": rule_id, "name": rule.name, "status": "created"}
