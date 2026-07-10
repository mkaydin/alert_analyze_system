import asyncio

import chromadb
import pytest

from app.config import settings
from app.core import rag_engine
from app.core.chroma_client import chroma
from app.core.embeddings import embed_client
from app.core.llm_client import llm_client

DIM = 8


@pytest.fixture
def store(tmp_path, monkeypatch):
    client = chromadb.PersistentClient(path=str(tmp_path / "chromadb"))
    for name in settings.chromadb_collections:
        client.get_or_create_collection(name)
    monkeypatch.setattr(chroma, "client", client, raising=False)
    monkeypatch.setattr(chroma, "_initialized", True, raising=False)
    return client


@pytest.fixture
def fake_ollama(monkeypatch):
    async def fake_embed(texts):
        return [[0.0] * DIM for _ in texts]

    async def fake_generate(prompt, system_prompt=""):
        return "GENERATED"

    monkeypatch.setattr(embed_client, "embed", fake_embed)
    monkeypatch.setattr(llm_client, "generate", fake_generate)


SAMPLE_JSON = (
    '{"id": "a1", "title": "Suspicious regsvr32", '
    '"description": "regsvr32 loading dll", "category": "Persistence", '
    '"severity": "high", "status": "new", "createdDateTime": "2026-02-26T10:55:20Z"}'
)


def test_analyze_input_json(store, fake_ollama):
    result = asyncio.run(rag_engine.analyze_input(SAMPLE_JSON, "auto"))
    assert result["input_type"] == "json"
    assert result["alert_id"] == "a1"
    assert result["analysis"] == "GENERATED"
    assert result["title"] == "Suspicious regsvr32"
    # ensure it was persisted and is retrievable
    assert rag_engine.load_alert_from_store("a1") is not None


def test_analyze_input_text_creates_synthetic_alert(store, fake_ollama):
    text = "powershell downloaded a payload from evil.com\nran as SYSTEM"
    result = asyncio.run(rag_engine.analyze_input(text, "auto"))
    assert result["input_type"] == "text"
    assert result["alert_id"].startswith("text_")
    assert result["title"] == "powershell downloaded a payload from evil.com"
    loaded = rag_engine.load_alert_from_store(result["alert_id"])
    assert loaded is not None
    assert "evil.com" in loaded.description


def test_analyze_input_empty_raises(store, fake_ollama):
    with pytest.raises(ValueError):
        asyncio.run(rag_engine.analyze_input("   ", "auto"))


def test_analyze_input_bad_json_forced(store, fake_ollama):
    with pytest.raises(ValueError):
        asyncio.run(rag_engine.analyze_input("not json", "json"))


def test_feedback_disapprove_stores_knowledge(store, fake_ollama):
    asyncio.run(rag_engine.analyze_input(SAMPLE_JSON, "auto"))
    result = asyncio.run(
        rag_engine.record_feedback(
            alert_id="a1",
            analysis="It is malicious",
            decision="disapprove",
            reason="This is a known benign FortiClient DLL load",
        )
    )
    assert result["stored"] is True
    assert result["decision"] == "disapprove"
    assert result["knowledge"] == "GENERATED"
    col = chroma.get_collection("feedback")
    assert col.count() == 1


def test_feedback_approve_no_llm_needed(store, fake_ollama):
    asyncio.run(rag_engine.analyze_input(SAMPLE_JSON, "auto"))
    result = asyncio.run(
        rag_engine.record_feedback(
            alert_id="a1", analysis="It is malicious", decision="approve"
        )
    )
    assert result["stored"] is True
    assert "APPROVED" in result["knowledge"]
    assert chroma.get_collection("feedback").count() == 1


def test_sanitize_strips_agentic_and_commands():
    raw = (
        "Let me examine the alert data first.\n"
        "cat /home/mka/Code/alert_analyze_system/AlertData.json\n"
        "file:///home/mka/Code/alert_analyze_system/AlertData.json\n"
        "## Verdict\n"
        "True Positive - powershell downloaded a payload."
    )
    cleaned = rag_engine._sanitize(raw)
    assert "Let me examine" not in cleaned
    assert "cat " not in cleaned
    assert "file://" not in cleaned
    assert "True Positive" in cleaned
    assert "## Verdict" in cleaned


def test_sanitize_keeps_normal_output():
    text = "## Summary\n\nThis alert is suspicious and needs review."
    assert rag_engine._sanitize(text) == text


def test_feedback_included_in_query_retrieval(store, fake_ollama):
    asyncio.run(rag_engine.analyze_input(SAMPLE_JSON, "auto"))
    asyncio.run(
        rag_engine.record_feedback(
            alert_id="a1", analysis="x", decision="disapprove", reason="benign"
        )
    )
    res = asyncio.run(rag_engine.query_rag("regsvr32", num_results=5))
    assert res["answer"] == "GENERATED"
