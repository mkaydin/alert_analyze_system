import uuid

from app.models.alert import Alert


class Chunk:
    def __init__(
        self,
        text: str,
        metadata: dict,
        collection: str,
        chunk_id: str | None = None,
    ):
        self.id = chunk_id or str(uuid.uuid4())
        self.text = text
        self.metadata = metadata
        self.collection = collection


def chunk_alert(alert: Alert) -> list[Chunk]:
    chunks = []

    summary_text = (
        f"Alert: {alert.title}\n"
        f"Description: {alert.description}\n"
        f"Category: {alert.category}\n"
        f"Severity: {alert.severity}\n"
        f"Status: {alert.status}\n"
        f"Detection: {alert.detection_source}\n"
        f"Created: {alert.created_datetime.isoformat() if alert.created_datetime else 'N/A'}"
    )
    chunks.append(
        Chunk(
            text=summary_text,
            metadata={
                "alert_id": alert.id,
                "type": "alert_summary",
                "category": alert.category,
                "severity": alert.severity,
                "status": alert.status,
                "incident_id": alert.incident_id or "",
                "detection_source": alert.detection_source,
                "created_datetime": (
                    alert.created_datetime.isoformat()
                    if alert.created_datetime
                    else ""
                ),
            },
            collection="alerts",
        )
    )

    for ev in alert.evidence:
        odata = ev.odata_type.lower()

        if "deviceevidence" in odata:
            detail = ev.details
            text = (
                f"Device: {detail.get('hostName', '')}\n"
                f"DNS: {detail.get('deviceDnsName', '')}\n"
                f"OS: {detail.get('osPlatform', '')} {detail.get('version', '')}\n"
                f"Risk: {detail.get('riskScore', '')}\n"
                f"Verdict: {ev.verdict}\n"
                f"IPs: {detail.get('lastIpAddress', '')} / {detail.get('lastExternalIpAddress', '')}\n"
                f"Onboarded: {detail.get('onboardingStatus', '')}"
            )
            chunks.append(
                Chunk(
                    text=text,
                    metadata={
                        "alert_id": alert.id,
                        "type": "evidence_device",
                        "hostName": detail.get("hostName", ""),
                        "osPlatform": detail.get("osPlatform", ""),
                        "verdict": ev.verdict or "",
                        "riskScore": detail.get("riskScore", ""),
                    },
                    collection="evidence",
                )
            )

        elif "processevidence" in odata:
            detail = ev.details
            image = detail.get("imageFile", {}) or {}
            user = detail.get("userAccount", {}) or {}
            text = (
                f"Process: {image.get('fileName', '')}\n"
                f"Command: {detail.get('processCommandLine', '')}\n"
                f"PID: {detail.get('processId', '')}\n"
                f"User: {user.get('accountName', '')}\n"
                f"Verdict: {ev.verdict}\n"
                f"SHA1: {image.get('sha1', '')}\n"
                f"SHA256: {image.get('sha256', '')}"
            )
            chunks.append(
                Chunk(
                    text=text,
                    metadata={
                        "alert_id": alert.id,
                        "type": "evidence_process",
                        "processName": image.get("fileName", ""),
                        "userAccount": user.get("accountName", ""),
                        "verdict": ev.verdict or "",
                    },
                    collection="evidence",
                )
            )

        elif "fileevidence" in odata:
            detail = ev.details
            text = (
                f"File: {detail.get('fileName', '')}\n"
                f"Path: {detail.get('filePath', '')}\n"
                f"SHA1: {detail.get('sha1', '')}\n"
                f"SHA256: {detail.get('sha256', '')}\n"
                f"Verdict: {ev.verdict}\n"
                f"FileSize: {detail.get('fileSize', '')}"
            )
            chunks.append(
                Chunk(
                    text=text,
                    metadata={
                        "alert_id": alert.id,
                        "type": "evidence_file",
                        "fileName": detail.get("fileName", ""),
                        "sha1": detail.get("sha1", ""),
                        "sha256": detail.get("sha256", ""),
                    },
                    collection="evidence",
                )
            )

        elif "registryevidence" in odata:
            detail = ev.details
            text = (
                f"Registry Key: {detail.get('registryKey', '')}\n"
                f"Registry Value: {detail.get('registryValue', '')}\n"
                f"Previous Value: {detail.get('previousRegistryValue', '')}\n"
                f"Verdict: {ev.verdict}"
            )
            chunks.append(
                Chunk(
                    text=text,
                    metadata={
                        "alert_id": alert.id,
                        "type": "evidence_registry",
                        "registryKey": detail.get("registryKey", ""),
                    },
                    collection="evidence",
                )
            )

    return chunks
