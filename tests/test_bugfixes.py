import asyncio
import uuid

import chromadb
import pytest

from app.config import settings
from app.core import rag_engine
from app.core.chroma_client import chroma
from app.core.embeddings import embed_client
from app.core.llm_client import llm_client
from app.ingestion.chunker import chunk_alert
from app.ingestion.parser import parse_alert_data
from app.models.alert import Alert


DIM = 8


def _emb():
    return [0.0] * DIM


@pytest.fixture
def store(tmp_path, monkeypatch):
    client = chromadb.PersistentClient(path=str(tmp_path / "chromadb"))
    for name in settings.chromadb_collections:
        client.get_or_create_collection(name)
    monkeypatch.setattr(chroma, "client", client, raising=False)
    monkeypatch.setattr(chroma, "_initialized", True, raising=False)
    return client


def _add_alert_to_store(alert: Alert):
    chunks = chunk_alert(alert)
    by_col: dict[str, list] = {}
    for c in chunks:
        by_col.setdefault(c.collection, []).append(c)
    for col_name, cs in by_col.items():
        col = chroma.get_collection(col_name)
        col.add(
            ids=[c.id for c in cs],
            embeddings=[_emb() for _ in cs],
            metadatas=[c.metadata for c in cs],
            documents=[c.text for c in cs],
        )


def _sample_alert(created="2026-02-26T10:55:20Z"):
    raw = {
        "id": "alert_123",
        "incidentId": "115",
        "title": "Potential WinAPI Calls Via CommandLine",
        "description": "scheduler.exe spawning regsvr32.exe as SYSTEM",
        "category": "Persistence",
        "severity": "high",
        "status": "new",
        "detectionSource": "MDE",
        "createdDateTime": created,
        "evidence": [
            {
                "@odata.type": "#microsoft.graph.security.deviceEvidence",
                "verdict": "Suspicious",
                "hostName": "supernova-1",
                "osPlatform": "Windows11",
            },
            {
                "@odata.type": "#microsoft.graph.security.processEvidence",
                "verdict": "Malicious",
                "imageFile": {"fileName": "regsvr32.exe", "sha256": "abc123"},
                "processCommandLine": "regsvr32.exe /s fccomintdll.dll",
                "userAccount": {"accountName": "SYSTEM"},
            },
        ],
    }
    return parse_alert_data(raw)[0]


def test_fix1_title_in_alert_metadata():
    alert = _sample_alert()
    chunks = chunk_alert(alert)
    summary = next(c for c in chunks if c.metadata["type"] == "alert_summary")
    assert summary.metadata["title"] == "Potential WinAPI Calls Via CommandLine"


def test_fix2_parser_handles_missing_datetime():
    raw = {"id": "x", "title": "t", "description": "d", "category": "c",
           "severity": "high", "status": "new"}
    alert = parse_alert_data(raw)[0]
    assert alert.created_datetime is None


def test_fix2_parser_handles_invalid_datetime():
    alert = _sample_alert(created="not-a-date")
    assert alert.created_datetime is None


def test_fix2_alert_model_allows_none_datetime():
    a = Alert(id="1", title="t", description="d", category="c",
              severity="high", status="new", detection_source="x",
              created_datetime=None)
    assert a.created_datetime is None


def test_fix2_load_alert_missing_datetime_no_crash(store):
    alert = _sample_alert(created="bad")
    _add_alert_to_store(alert)
    loaded = rag_engine.load_alert_from_store("alert_123")
    assert loaded is not None
    assert loaded.created_datetime is None


def test_fix1and3_load_alert_has_title_and_evidence(store):
    alert = _sample_alert()
    _add_alert_to_store(alert)
    loaded = rag_engine.load_alert_from_store("alert_123")
    assert loaded.title == "Potential WinAPI Calls Via CommandLine"
    assert len(loaded.evidence) == 2
    assert loaded.category == "Persistence"


def test_load_alert_not_found(store):
    assert rag_engine.load_alert_from_store("nope") is None


def test_fix3_summarize_includes_evidence(store, monkeypatch):
    captured = {}

    async def fake_generate(prompt, system_prompt=""):
        captured["prompt"] = prompt
        return "SUMMARY"

    monkeypatch.setattr(llm_client, "generate", fake_generate)

    alert = _sample_alert()
    _add_alert_to_store(alert)
    loaded = rag_engine.load_alert_from_store("alert_123")

    result = asyncio.run(rag_engine.summarize_alert(loaded, fmt="concise"))
    assert result["summary"] == "SUMMARY"
    assert "regsvr32.exe" in captured["prompt"]
    assert "No evidence" not in captured["prompt"]


def test_fix4_documents_list_counts_chunks(store):
    from app.api.routes.documents import list_documents

    col = chroma.get_collection("documents")
    col.add(
        ids=[str(uuid.uuid4()) for _ in range(3)],
        embeddings=[_emb() for _ in range(3)],
        metadatas=[
            {"title": "MITRE Guide", "source": "mitre-attack"},
            {"title": "MITRE Guide", "source": "mitre-attack"},
            {"title": "LOLBins", "source": "lolbins"},
        ],
        documents=["a", "b", "c"],
    )

    result = asyncio.run(list_documents())
    assert result["total"] == 2
    by_title = {d["title"]: d for d in result["documents"]}
    assert by_title["MITRE Guide"]["chunks"] == 2
    assert by_title["LOLBins"]["chunks"] == 1


def test_fix5_client_stats_shape():
    for stats in (embed_client.stats(), llm_client.stats()):
        assert set(stats.keys()) == {"active", "max", "queue"}
        assert stats["max"] == settings.ollama_concurrency
        assert stats["active"] >= 0
        assert stats["queue"] >= 0
