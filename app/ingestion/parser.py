from datetime import datetime

from app.models.alert import Alert, AlertEvidence


def parse_alert_data(raw: dict) -> list[Alert]:
    values = extract_values(raw)
    return [_parse_single(v) for v in values]


def extract_values(raw: dict) -> list[dict]:
    if "value" in raw:
        return raw["value"]
    data_block = raw.get("data", raw)
    if "value" in data_block:
        return data_block["value"]
    if isinstance(data_block, list):
        return data_block
    return [data_block]


def _parse_single(item: dict) -> Alert:
    evidence = []
    for ev in item.get("evidence", []):
        evidence.append(
            AlertEvidence(
                odata_type=ev.get("@odata.type", ""),
                verdict=ev.get("verdict"),
                remediation_status=ev.get("remediationStatus"),
                details=_flatten_evidence(ev),
            )
        )

    return Alert(
        id=item.get("id", ""),
        incident_id=item.get("incidentId"),
        title=item.get("title", ""),
        description=item.get("description", ""),
        category=item.get("category", ""),
        severity=item.get("severity", ""),
        status=item.get("status", ""),
        detection_source=item.get("detectionSource", ""),
        product_name=item.get("productName", ""),
        service_source=item.get("serviceSource", ""),
        created_datetime=_parse_dt(item.get("createdDateTime")),
        first_activity_datetime=_parse_dt(item.get("firstActivityDateTime")),
        last_activity_datetime=_parse_dt(item.get("lastActivityDateTime")),
        mitre_techniques=item.get("mitreTechniques", []),
        evidence=evidence,
        tags=item.get("tags", []),
        comments=item.get("comments", []),
        alert_web_url=item.get("alertWebUrl"),
    )


def _flatten_evidence(ev: dict) -> dict:
    result = {}
    for k, v in ev.items():
        if k in ("@odata.type", "verdict", "remediationStatus"):
            continue
        result[k] = v
    return result


def _parse_dt(val: str | None) -> datetime | None:
    if val is None:
        return None
    try:
        return datetime.fromisoformat(val.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
