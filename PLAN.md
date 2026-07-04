# Plan: Local RAG LLM System for Security Alert Analysis

> **Stack:** FastAPI + ChromaDB + Ollama (LLM + Embeddings)
> **Goal:** Ingest Microsoft Defender alerts (AlertData.json), store them as vector embeddings, query/summarize/analyze via natural language, all fully local.

---

## 1. Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                         FastAPI Server                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────────┐  │
│  │ /ingest  │  │ /query   │  │/summarize│  │ /analyze        │  │
│  │ /alerts  │  │ /rules   │  │ /health  │  │ /stats          │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───────┬─────────┘  │
│       └──────────────┼──────────────┼───────────────┘             │
│                      ▼              ▼                             │
│  ┌─────────────────────────────────────────────────────┐          │
│  │                   RAG Engine                         │          │
│  │  ┌──────────┐   ┌──────────┐   ┌──────────────────┐ │          │
│  │  │ Retrieval│   │  Prompt  │   │   Response Gen   │ │          │
│  │  │ (Chroma) │──▶│ Assembly │──▶│  (Ollama LLM)    │ │          │
│  │  └──────────┘   └──────────┘   └──────────────────┘ │          │
│  └─────────────────────────────────────────────────────┘          │
│                                    │                              │
│  ┌─────────────────────────────────────────────────────┐          │
│  │              Concurrency Controller                  │          │
│  │       asyncio.Semaphore(OLLAMA_CONCURRENCY)          │          │
│  │    ┌──────────────┐         ┌──────────────────┐    │          │
│  │    │ Ollama Embed │         │  Ollama LLM      │    │          │
│  │    │ (batched)    │         │  (queued)        │    │          │
│  │    └──────┬───────┘         └────────┬─────────┘    │          │
│  └───────────┼──────────────────────────┼──────────────┘          │
│              │                          │                          │
└──────────────┼──────────────────────────┼──────────────────────────┘
               │                          │
               ▼                          ▼
        ┌──────────────┐         ┌──────────────────┐
        │   Ollama     │         │    Ollama        │
        │  Embeddings  │         │    LLM           │
         │  (nomic-     │         │  (ornith,         │
         │   embed-text)│         │   mistral, etc)   │
        └──────────────┘         └──────────────────┘
               │
               ▼
        ┌──────────────┐
        │   ChromaDB   │
        │  (persistent)│
        │ ┌──────────┐ │
        │ │ alerts   │ │
        │ │ evidence │ │
        │ │ rules    │ │
        │ │ flags    │ │
        │ └──────────┘ │
        └──────────────┘
```

---

## 2. Directory Structure

```
alert_analyze_system/
├── PLAN.md
├── requirements.txt
├── .env                          # Ollama config, concurrency settings
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI app, lifespan, middleware
│   ├── config.py                 # Pydantic Settings loader
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── ingest.py         # POST /ingest, /ingest/batch
│   │   │   ├── alerts.py         # GET/DELETE /alerts, /alerts/{id}
│   │   │   ├── query.py          # POST /query
│   │   │   ├── summarize.py      # POST /summarize
│   │   │   ├── analyze.py        # POST /analyze
│   │   │   ├── rules.py          # GET/POST /rules
│   │   │   └── health.py         # GET /health, /stats
│   │   └── deps.py               # Dependency injection (get_db, get_llm)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── rag_engine.py         # Orchestration: retrieve → prompt → generate
│   │   ├── embeddings.py         # Ollama embed client (batched, rate-limited)
│   │   ├── llm_client.py         # Ollama LLM client (semaphore-guarded)
│   │   └── chroma_client.py      # ChromaDB singleton wrapper
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── parser.py             # AlertData.json → normalized dicts
│   │   ├── chunker.py            # Chunking strategies per document type
│   │   └── ingestor.py           # Pipeline: parse → chunk → embed → store
│   └── models/
│       ├── __init__.py
│       ├── alert.py              # Pydantic: Alert, AlertCollection
│       ├── evidence.py           # Pydantic: DeviceEvidence, ProcessEvidence
│       ├── query.py              # Pydantic: QueryRequest, QueryResponse
│       └── rule.py               # Pydantic: DetectionRule
├── data/
│   ├── chromadb/                 # ChromaDB persistent storage (gitignored)
│   └── samples/                  # Sample alert JSONs
└── tests/
    ├── __init__.py
    ├── conftest.py
    └── test_*.py
```

---

## 3. Data Model (Pydantic)

### 3.1 Alert Models — `app/models/alert.py`

```python
class AlertEvidence(BaseModel):
    odata_type: str                        # e.g. "#microsoft.graph.security.deviceEvidence"
    verdict: str | None
    remediation_status: str | None
    # Evidence-specific fields are stored as flat dict for flexibility
    details: dict[str, Any]

class Alert(BaseModel):
    id: str                                # e.g. "ed639077001205960280_718389113"
    incident_id: str | None
    title: str
    description: str
    category: str                          # Persistence, Execution, etc.
    severity: str                          # high, medium, low, informational
    status: str                            # new, resolved, etc.
    detection_source: str
    product_name: str
    service_source: str
    created_datetime: datetime
    first_activity_datetime: datetime | None
    last_activity_datetime: datetime | None
    mitre_techniques: list[str]
    evidence: list[AlertEvidence]
    tags: list[str]
    comments: list[dict]
    alert_web_url: str | None

class AlertCollection(BaseModel):
    total_count: int
    alerts: list[Alert]
```

### 3.2 Query Models — `app/models/query.py`

```python
class QueryRequest(BaseModel):
    query: str                             # Natural language question
    num_results: int = 5                   # Chunks to retrieve
    filters: dict[str, str] | None = None  # e.g. {"category": "Persistence"}
    model: str = "ornith:latest"               # Ollama model name

class QueryResponse(BaseModel):
    answer: str
    sources: list[dict]                    # Retrieved chunks with metadata
    processing_time_ms: int

class SummarizeRequest(BaseModel):
    alert_ids: list[str]                   # Specific alert IDs
    format: str = "concise"                # concise / detailed / soc-report

class AnalyzeRequest(BaseModel):
    alert_id: str
    include_similar: bool = True           # Retrieve similar past alerts
```

### 3.3 Rule Models — `app/models/rule.py`

```python
class DetectionRule(BaseModel):
    id: str | None
    name: str
    description: str
    category: str                          # Matches alert category
    severity: str
    mitre_techniques: list[str]
    indicators: list[str]                  # Patterns in command line, registry, etc.
    iocs: list[str]                        # Known bad hashes, IPs, domains
```

---

## 4. API Endpoints

### 4.1 Health & Stats

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/health` | LLM status, ChromaDB status, uptime |
| `GET` | `/api/v1/stats` | Alert count by category, severity, status |

**`GET /api/v1/health` → Response:**
```json
{
  "status": "healthy",
  "ollama": {
    "reachable": true,
    "models": ["ornith:latest", "nomic-embed-text:latest"],
    "concurrency": { "active": 2, "max": 4, "queue": 1 }
  },
  "chromadb": { "status": "connected", "collections": 4, "documents": 47 }
}
```

### 4.2 Ingestion

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/ingest` | Ingest a single alert or the full AlertData.json envelope |
| `POST` | `/api/v1/ingest/batch` | Ingest multiple alert objects at once |

**`POST /api/v1/ingest` → Request Body:**
```json
{
  "source": "file",
  "data": { /* AlertData.json content or single alert object */ },
  "chunk_strategy": "per_evidence"
}
```

**↳ Response:**
```json
{
  "ingested": 1,
  "chunks_created": 5,
  "collection": "alerts",
  "alert_ids": ["ed639077001205960280_718389113"]
}
```

**Ingestion pipeline (internal):**
```
Raw JSON → Parser.parse() → list[Alert] → Chunker.chunk(alert)
  → per alert: 1 summary chunk
  → per evidence: 1 evidence chunk
  → embed each chunk via Ollama (batched) → store in ChromaDB
```

### 4.3 Alert Retrieval

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/alerts` | List alerts with optional filters |
| `GET` | `/api/v1/alerts/{id}` | Retrieve full alert by ID |
| `DELETE` | `/api/v1/alerts/{id}` | Remove an alert and its chunks |

**`GET /api/v1/alerts?category=Persistence&severity=high&limit=20`**
```json
{
  "total": 78,
  "limit": 20,
  "offset": 0,
  "alerts": [
    {
      "id": "ed639077001205960280_718389113",
      "title": "Potential WinAPI Calls Via CommandLine",
      "category": "Persistence",
      "severity": "high",
      "status": "new",
      "created_datetime": "2026-02-26T10:55:20Z",
      "evidence_count": 5
    }
  ]
}
```

### 4.4 Query (RAG)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/query` | Natural language query over ingested alerts |

**`POST /api/v1/query`**
```json
{
  "query": "Show me all persistence alerts on supernova-1 involving regsvr32",
  "num_results": 5,
  "filters": { "hostName": "supernova-1" },
  "model": "ornith:latest"
}
```

**↳ RAG flow:**
```
1. Embed query via Ollama (nomic-embed-text:latest)
2. ChromaDB similarity search across 'alerts' + 'evidence' collections
3. Filter results by metadata (hostName, category)
4. Assemble prompt with retrieved context
5. LLM generate → return answer + sources
```

**↳ Response:**
```json
{
  "answer": "Found 1 relevant alert (ID: ed63907...). The alert 'Potential WinAPI Calls Via CommandLine' on supernova-1 shows scheduler.exe spawning regsvr32.exe to silently load a FortiClient DLL. This occurred twice (Feb 26 and Feb 28). Both processes ran as SYSTEM. The pattern suggests a persistence mechanism using LOLBins.",
  "sources": [
    { "chunk_id": "chunk_ev_001", "alert_id": "ed63907...", "type": "evidence", "relevance": 0.92 },
    { "chunk_id": "chunk_alert_001", "alert_id": "ed63907...", "type": "alert_summary", "relevance": 0.85 }
  ],
  "processing_time_ms": 2340
}
```

### 4.5 Summarize

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/summarize` | LLM-generated summary of specific alerts |

**`POST /api/v1/summarize`**
```json
{
  "alert_ids": ["ed639077001205960280_718389113"],
  "format": "soc-report"
}
```

**↳ Response:**
```json
{
  "alert_id": "ed639077001205960280_718389113",
  "summary": {
    "title": "Potential WinAPI Calls Via CommandLine",
    "verdict": "Suspicious - needs investigation",
    "key_findings": [
      "Unsigned binary scheduler.exe executing WinAPI calls as SYSTEM",
      "regsvr32.exe used in silent mode to load fccomintdll.dll (LOLBins technique)",
      "Activity recurred after 2 days indicating persistence mechanism"
    ],
    "affected_assets": ["supernova-1 (Windows 11 23H2, user: merto)"],
    "mitre_mapping": ["T1543.003 (Create or Modify System Process)", "T1218.010 (Regsvr32)"],
    "recommended_actions": [
      "Quarantine scheduler.exe and investigate origin",
      "Check FortiClient DLL integrity on supernova-1",
      "Review scheduled tasks created around Feb 26",
      "Escalate to Incident #115"
    ]
  }
}
```

### 4.6 Analyze

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/analyze` | Classify alert + enrich with similar historical alerts |

**`POST /api/v1/analyze`**
```json
{
  "alert_id": "ed639077001205960280_718389113",
  "include_similar": true
}
```

**↳ Flow:**
```
1. Retrieve Alert from ChromaDB
2. Embed alert summary → find top-K similar historical alerts
3. Send alert + similar alerts + analysis prompt to LLM
4. Return classification with supporting evidence
```

### 4.7 Rules Management

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/rules` | List all detection rules |
| `POST` | `/api/v1/rules` | Add a detection rule |

**`POST /api/v1/rules`**
```json
{
  "name": "Regsvr32 LOLBins Detection",
  "description": "Detects regsvr32.exe used with /s (silent) or /i flags outside normal hours",
  "category": "Execution",
  "severity": "high",
  "mitre_techniques": ["T1218.010"],
  "indicators": [
    "regsvr32.exe /s *",
    "regsvr32.exe /i:*"
  ],
  "iocs": []
}
```

---

## 5. Chunking Strategy — `app/ingestion/chunker.py`

Each Alert produces **multiple chunks** to enable granular retrieval:

### Chunk Types

| Chunk Type | Content | Metadata | ChromaDB Collection |
|------------|---------|----------|---------------------|
| `alert_summary` | Title + description + category + severity | `alert_id`, `type`, `category`, `severity`, `status`, `incident_id` | `alerts` |
| `evidence_device` | Device name, OS, IPs, risk score, verdict | `alert_id`, `type`, `hostName`, `osPlatform`, `verdict`, `riskScore` | `evidence` |
| `evidence_process` | Process name, command line, PID, user, verdict | `alert_id`, `type`, `processName`, `userAccount`, `verdict`, `parentProcessId` | `evidence` |
| `evidence_file` | File name, path, hashes | `alert_id`, `type`, `sha1`, `sha256` | `evidence` |

### Chunking Logic

```python
# Pseudocode
def chunk_alert(alert: Alert) -> list[Chunk]:
    chunks = []

    # 1. Alert summary chunk (always)
    chunks.append(Chunk(
        text=f"Alert: {alert.title}\n{alert.description}\nCategory: {alert.category}\nSeverity: {alert.severity}",
        metadata={"alert_id": alert.id, "type": "alert_summary", "category": alert.category, ...},
        collection="alerts"
    ))

    # 2. Per-evidence chunks
    for ev in alert.evidence:
        if ev.odata_type.contains("deviceEvidence"):
            chunks.append(Chunk(
                text=f"Device: {ev.details['hostName']}\nOS: {ev.details['osPlatform']} {ev.details.get('version', '')}\nRisk: {ev.details.get('riskScore')}\nIPs: {ev.details.get('lastIpAddress')} / {ev.details.get('lastExternalIpAddress')}",
                metadata={"alert_id": alert.id, "type": "evidence_device", "hostName": ev.details.get("hostName")},
                collection="evidence"
            ))
        elif ev.odata_type.contains("processEvidence"):
            chunks.append(Chunk(
                text=f"Process: {ev.details['imageFile']['fileName']}\nCommand: {ev.details.get('processCommandLine', '')}\nPID: {ev.details.get('processId')}\nUser: {ev.details.get('userAccount', {}).get('accountName')}\nVerdict: {ev.verdict}",
                metadata={"alert_id": alert.id, "type": "evidence_process", "processName": ev.details["imageFile"]["fileName"]},
                collection="evidence"
            ))

    return chunks
```

---

## 6. Concurrency & Ollama Integration

### 6.1 Configuration — `app/config.py`

```python
class Settings(BaseSettings):
    # Ollama
    ollama_host: str = "http://localhost:11434"
    embed_model: str = "nomic-embed-text:latest"
    llm_model: str = "ornith:latest"
    ollama_concurrency: int = 4       # Max parallel requests to Ollama
    ollama_timeout: int = 60          # Per-request timeout
    llm_temperature: float = 0.1      # Low temp for deterministic analysis
    llm_max_tokens: int = 2048

    # ChromaDB
    chromadb_path: str = "data/chromadb"
    chromadb_collections: list[str] = ["alerts", "evidence", "rules", "flags"]
```

### 6.2 Concurrency Controller — `app/core/embeddings.py` & `app/core/llm_client.py`

Two **independent** semaphores to avoid head-of-line blocking:
- `embed_semaphore = asyncio.Semaphore(config.ollama_concurrency)` for embedding
- `llm_semaphore = asyncio.Semaphore(config.ollama_concurrency)` for generation

```python
# Pseudocode for concurrent Ollama client
class OllamaEmbedClient:
    def __init__(self, config):
        self.semaphore = asyncio.Semaphore(config.ollama_concurrency)
        self.client = AsyncOllamaClient(config.ollama_host)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed texts with batching + concurrency control."""
        async with self.semaphore:
            response = await self.client.embeddings(
                model=config.embed_model,
                prompt=texts,          # Ollama supports list input
                options={"num_thread": 4}
            )
        return [r["embedding"] for r in response["embeddings"]]

class OllamaLLMClient:
    def __init__(self, config):
        self.semaphore = asyncio.Semaphore(config.ollama_concurrency)
        self.client = AsyncOllamaClient(config.ollama_host)

    async def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate with concurrency control."""
        async with self.semaphore:
            response = await self.client.generate(
                model=config.llm_model,
                prompt=prompt,
                system=system_prompt,
                options={
                    "temperature": config.llm_temperature,
                    "num_predict": config.llm_max_tokens
                }
            )
        return response["response"]
```

### 6.3 Embedding Batching Strategy

For ingestion, texts are collected and sent to Ollama in batches:

```python
# app/ingestion/ingestor.py
async def ingest_alerts(alerts: list[Alert]):
    chunks = []
    for alert in alerts:
        chunks.extend(chunker.chunk_alert(alert))

    # Batch embed — maximum batch size = OLLAMA_CONCURRENCY * 2
    batch_size = config.ollama_concurrency * 2
    all_embeddings = []
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        texts = [c.text for c in batch]
        embeddings = await embed_client.embed(texts)
        all_embeddings.extend(embeddings)

    # Store in ChromaDB
    await chroma_client.add(
        collection="alerts",
        ids=[c.id for c in chunks],
        embeddings=all_embeddings,
        metadatas=[c.metadata for c in chunks],
        documents=[c.text for c in chunks]
    )
```

### 6.4 Concurrency Flow Diagram

```
Request A ──▶ /query ──▶ embed query ──▶ (acquire embed_sem) ──▶ Ollama Embed ──▶ ...
                                            │ wait if busy
Request B ──▶ /summarize ──▶ llm call ──▶ (acquire llm_sem) ──▶ Ollama LLM ──▶ ...
                                            │ wait if busy
Request C ──▶ /ingest ──▶ embed batches ──▶ (acquire embed_sem) ──▶ Ollama Embed ──▶ ...
```

**Behavior under load:**
- If `OLLAMA_CONCURRENCY=4`, at most 4 Ollama calls run simultaneously (across all endpoints)
- Embedding requests wait for embed_semaphore
- LLM generation requests wait for llm_semaphore
- Each semaphore is independent — an embedding won't block a generation slot and vice versa
- FastAPI's async nature allows other requests to be queued/accepted while waiting

---

## 7. Prompt Templates

### 7.1 Query Prompt — `app/core/rag_engine.py`

```
System: You are a SOC analyst assistant. Answer questions about security alerts
using the provided context. Be precise and cite alert IDs when referencing evidence.
If the context doesn't contain enough information, say so.

Context:
{retrieved_chunks}

Question: {query}

Answer concisely. Include:
- Which alerts are relevant
- Key findings (processes, devices, IOCs)
- Risk assessment
```

### 7.2 Summarize Prompt

```
System: Generate a structured SOC report summary for the given alert.

Alert:
- Title: {title}
- Category: {category}
- Severity: {severity}
- Description: {description}
- Detection: {detection_source}
- Status: {status}

Evidence:
{evidence_text}

Produce a summary with:
1. One-line verdict (True Positive / Suspicious / Benign)
2. Key findings bullet list
3. Affected assets
4. Mapped MITRE ATT&CK techniques (infer from context)
5. Recommended actions
```

### 7.3 Analyze Prompt

```
System: Classify this alert and compare it against similar historical alerts.

Current Alert:
{alert_summary}

Similar Historical Alerts:
{similar_alerts_context}

Provide:
1. Classification: True Positive / False Positive / Suspicious / Needs Review
2. Confidence (0-100%)
3. Similar incidents found (if any) — are they related?
4. Suggested priority adjustment (1-10)
5. Specific next steps
```

---

## 8. ChromaDB Collection Schema

| Collection | Documents | Metadata Fields |
|------------|-----------|-----------------|
| `alerts` | Alert summary text | `alert_id`, `type: "alert_summary"`, `category`, `severity`, `status`, `incident_id`, `detection_source`, `created_datetime` |
| `evidence` | Evidence description text | `alert_id`, `type: "evidence_{device,process,file}"`, `hostName`, `processName`, `verdict`, `osPlatform`, `userAccount`, `timestamp` |
| `rules` | Rule description | `rule_id`, `name`, `category`, `severity`, `mitre_techniques` |
| `flags` | System flag description | `flag_id`, `name`, `type: "ioc" / "pattern" / "indicator"`, `severity` |

---

## 9. Ingestion Pipeline Flow

```
AlertData.json / batch
        │
        ▼
┌───────────────┐
│  Parser       │  Normalizes fields, flattens nested evidence
│  (parser.py)  │  Returns list[Alert]
└───────┬───────┘
        │
        ▼
┌───────────────┐
│  Chunker      │  Splits each Alert into multiple Chunk objects
│  (chunker.py) │  Returns list[Chunk] with metadata
└───────┬───────┘
        │
        ▼
┌───────────────┐
│  Embedder     │  Batches texts → calls Ollama Embeddings
│  (embeddings) │  Returns list[list[float]]
└───────┬───────┘
        │
        ▼
┌───────────────┐
│  ChromaDB     │  Stores (id, embedding, metadata, document)
│  (ingestor)   │  Per-collection upsert
└───────────────┘
```

---

## 10. Implementation Phases

### Phase 1 — Foundation (MVP)
- [ ] `config.py` — settings + env loading
- [ ] `core/embeddings.py` — Ollama embed client with semaphore
- [ ] `core/llm_client.py` — Ollama LLM client with semaphore
- [ ] `core/chroma_client.py` — ChromaDB singleton (create collections on startup)
- [ ] `models/` — Pydantic schemas for Alert, Query, Rule
- [ ] `ingestion/parser.py` — Parse AlertData.json into Alert objects
- [ ] `ingestion/chunker.py` — Chunk alerts by summary + per evidence
- [ ] `ingestion/ingestor.py` — Wire up parse → chunk → embed → store
- [ ] `api/routes/ingest.py` — /ingest endpoint
- [ ] `api/routes/health.py` — /health endpoint
- [ ] `main.py` — FastAPI app with lifespan startup

### Phase 2 — RAG Query
- [ ] `core/rag_engine.py` — Retrieve → prompt → generate pipeline
- [ ] `api/routes/query.py` — /query endpoint
- [ ] `api/routes/alerts.py` — /alerts listing with filters
- [ ] Prompt templates for query/summarize/analyze

### Phase 3 — Analysis & Rules
- [ ] `api/routes/summarize.py` — /summarize endpoint
- [ ] `api/routes/analyze.py` — /analyze endpoint
- [ ] `api/routes/rules.py` — Rules CRUD
- [ ] Rule matching engine (check alert against stored rules)

### Phase 4 — Polish
- [ ] Error handling & retry with exponential backoff
- [ ] Request logging middleware
- [ ] Stats endpoint (by category, severity, timeline)
- [ ] Tests for each module
- [ ] CLI convenience script for quick ingestion

---

## 11. Dependencies — `requirements.txt`

```
fastapi>=0.115.0
uvicorn[standard]>=0.34.0
pydantic>=2.10.0
pydantic-settings>=2.6.0
chromadb>=0.6.0
httpx>=0.28.0              # Async HTTP for Ollama
python-dotenv>=1.0.0
```
(No Ollama SDK needed — use raw httpx calls to Ollama's HTTP API)

---

## 12. Edge Cases & Constraints

| Concern | Mitigation |
|---------|------------|
| Ollama not running | `/health` returns `ollama.reachable: false`; ingestion/query returns 503 |
| Ollama model not pulled | Auto-check on startup; return clear error message |
| Large alert batch (>100 alerts) | Stream ingestion; process in background task with task ID |
| Empty evidence array | Skip chunking; store only alert summary chunk |
| Duplicate alert IDs | ChromaDB upsert by ID (idempotent) |
| Concurrent Ollama overload | Semaphore limits parallel calls; requests queue in asyncio |
| ChromaDB persistence corruption | Regular backup of `data/chromadb/`; add health check |
| Long LLM generation | Configurable max_tokens; stream response for chat |
| Malformed JSON in request | Pydantic validation returns 422 with details |
| Query with no matches | Return "No relevant alerts found" with suggestion to broaden query |

---

## 13. Quickstart (for developer)

```bash
# 1. Ensure Ollama is running with required models
ollama pull nomic-embed-text:latest
ollama pull ornith:latest

# 2. Install deps
pip install -r requirements.txt

# 3. Launch API
uvicorn app.main:app --reload --port 8000

# 4. Ingest test data
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d @AlertData.json

# 5. Query
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What persistence mechanisms were detected on supernova-1?"}'
```

---

## 14. Prompt Templates Reference File

For easy maintenance, store prompts in `app/core/prompts.toml` or `app/core/prompts.py`:

```python
# app/core/prompts.py

QUERY_PROMPT = """\
System: You are a SOC analyst assistant. Answer questions about security alerts
using the provided context. Be precise and cite alert IDs when referencing evidence.
If the context doesn't contain enough information, say so.

Context:
{retrieved_chunks}

Question: {query}

Answer concisely. Include:
- Which alerts are relevant
- Key findings (processes, devices, IOCs)
- Risk assessment
"""

SUMMARIZE_PROMPT = """\
System: Generate a structured SOC report summary for the given alert.

Alert:
- Title: {title}
- Category: {category}
- Severity: {severity}
- Description: {description}
- Detection: {detection_source}
- Status: {status}

Evidence:
{evidence_text}

Produce a summary with:
1. One-line verdict (True Positive / Suspicious / Benign)
2. Key findings bullet list
3. Affected assets
4. Mapped MITRE ATT&CK techniques (infer from context)
5. Recommended actions
"""

ANALYZE_PROMPT = """\
System: Classify this alert and compare it against similar historical alerts.

Current Alert:
{alert_summary}

Similar Historical Alerts:
{similar_alerts_context}

Provide:
1. Classification: True Positive / False Positive / Suspicious / Needs Review
2. Confidence (0-100%)
3. Similar incidents found (if any) — are they related?
4. Suggested priority adjustment (1-10)
5. Specific next steps
"""
```
