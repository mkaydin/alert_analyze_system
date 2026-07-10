# Alert Analysis RAG System

A fully-local Retrieval-Augmented Generation (RAG) system for analyzing Microsoft Defender security alerts. Ingests Defender alert JSON, chunks and embeds evidence into ChromaDB, then answers natural language questions via Ollama — all offline, no cloud APIs.

## Architecture

```
                         FastAPI Server
  ┌──────────────────────────────────────────────────────────────────┐
  │  POST /ingest       POST /query       POST /summarize            │
  │  POST /analyze      POST /categorize  POST /ingest-document      │
  │  GET /alerts        GET /alerts/{id}  DELETE /alerts/{id}        │
  │  GET /rules         POST /rules       GET/POST /documents/*      │
  │  GET /health        GET /stats                                   │
  └──────────────────────────────────────────────────────────────────┘
                           │
                           ▼
  ┌───────────────────────────────────────────────────────────────┐
  │                     RAG Engine                                │
  │  [Retrieval (ChromaDB)] → [Prompt Assembly] → [LLM (Ollama)]  │
  └───────────────────────────────────────────────────────────────┘
                     │                       │
                     ▼                       ▼
              ┌──────────────┐       ┌──────────────────┐
              │  qwen3-embed │       │   ornith:latest  │
              │  (1024d emb) │       │   (LLM, 4B param)│
              └──────┬───────┘       └────────┬─────────┘
                     │                        │
                     ▼                        ▼
              ┌───────────────────────────────────────┐
              │           ChromaDB (persistent)       │
              │  ┌──────┬────────┬──────┬──────┬────┐ │
              │  │alerts│evidence│ rules│flags │doc │ │
              │  └──────┴────────┴──────┴──────┴────┘ │
              └───────────────────────────────────────┘
```

## Features

- **Alert ingestion** — Parse Microsoft Defender `AlertData.json`, chunk by alert summary + per-evidence entry, embed and store in ChromaDB
- **Natural language query** — Ask questions about threats, processes, devices, IOCs. RAG retrieves relevant chunks from 5 collections and generates answers via LLM
- **Summarization** — Generate SOC-report-style summaries (concise, detailed, or soc-report format)
- **Alert analysis & categorization** — Classify alerts (TP/FP/Suspicious), compare against similar historical alerts, assign MITRE ATT&CK tactics
- **Reference document ingestion** — Load MITRE ATT&CK guides, LOLBins playbooks, SOC response procedures as searchable markdown documents
- **CLI client** — 15+ commands: `ingest`, `query`, `summarize`, `analyze`, `categorize`, `alerts`, `rules`, `health`, `stats`, `doc-load`, `doc-list`, and more
- **STIX bundle ingestion** — Bulk-ingest MITRE ATT&CK enterprise/ICS/mobile technique data (850+ techniques)
- **Concurrency control** — Independent semaphores for embedding and LLM calls prevent Ollama overload
- **100% local** — No external API calls. ChromaDB persists to disk. Works disconnected.

## Quick Start

### Prerequisites

- Python 3.12+
- [Ollama](https://ollama.ai) running with required models:

```bash
ollama pull qwen3-embedding:0.6b
ollama pull ornith:latest
```

### Setup

```bash
# Clone and install
pip install -r requirements.txt

# Configure
cp .env.example .env   # or edit .env directly

# Start the server
uvicorn app.main:app --port 8002 --reload

# Check health
python client.py health
```

### Ingestion & Query

```bash
# 1. Ingest a Defender alert JSON
python client.py ingest AlertData.json

# 2. Ask questions
python client.py query "What persistence mechanisms were detected?"
python client.py query "Show all processes running as SYSTEM"

# 3. Summarize & analyze
python client.py summarize <alert_id>
python client.py analyze <alert_id>
python client.py categorize <alert_id>

# 4. List & manage
python client.py alerts --severity high
python client.py alerts --category Persistence --limit 20
```

### Reference Documents

```bash
# Load built-in MITRE, LOLBins, and playbook documents
python client.py doc-load-ref

# Or load your own
python client.py doc-load data/documents/your_folder

# List loaded documents
python client.py doc-list
```

### STIX Bundle Test (MITRE ATT&CK)

```bash
# Ingest 100 techniques per domain (enterprise/ICS/mobile)
python tests/test_stix_ingestion.py --max 100

# Full ingestion (all 858 enterprise + 118 ICS + 190 mobile)
python tests/test_stix_ingestion.py

# Speed comparison between embedding models:
#   nomic-embed-text:  ~39 docs/sec,  768 dims
#   qwen3-embedding:0.6b: ~117 docs/sec, 1024 dims
```

## Desktop GUI (PySide6)

A cross-platform desktop client (Linux/macOS/Windows) for the analyze → review → learn workflow.

```bash
# Install GUI deps (into the same venv)
pip install -r gui/requirements-gui.txt

# Make sure the API server is running (see Quick Start), then:
python -m gui.app
```

Workflow:
1. Paste a Defender alert JSON or plain-text description (or **Load JSON file…**), pick a type (`auto`/`json`/`text`), click **Analyze**.
2. The analysis + summary render in the result pane.
3. Click **Approve** (recorded) or **Disapprove** → a reason box opens; your reason is sent back, the AI distills a lesson, and it's added to the system's knowledge (`feedback` collection) for future analyses.

Server URL is configurable via **Settings → Set server URL…** or the `ALERT_GUI_BASE_URL` env var (default `http://localhost:8002`).

**Packaging** (per OS):
```bash
pyinstaller --onefile --windowed --name alert-analyzer gui/app.py
```

## Configuration

All settings in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `ALERT_OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `ALERT_EMBED_MODEL` | `qwen3-embedding:0.6b` | Embedding model (1024-dim, tested) |
| `ALERT_LLM_MODEL` | `ornith:latest` | LLM for generation |
| `ALERT_OLLAMA_CONCURRENCY` | `4` | Max parallel Ollama requests |
| `ALERT_OLLAMA_TIMEOUT` | `60` | Per-request timeout (s) |
| `ALERT_LLM_TEMPERATURE` | `0.1` | Low temp for deterministic output |
| `ALERT_LLM_MAX_TOKENS` | `2048` | Max generated tokens |
| `ALERT_CHROMADB_PATH` | `data/chromadb` | ChromaDB persistent storage |

## API Reference

### Health & Stats

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/health` | Server status, Ollama models, ChromaDB collections |
| `GET` | `/api/v1/stats` | Alert counts by category, severity, status |

### Alert Ingestion

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/ingest` | Ingest AlertData.json (single alert or batch) |

Request body: the raw AlertData.json. Response:
```json
{
  "ingested": 1,
  "chunks_created": 5,
  "alert_ids": ["ed639077001205960280_718389113"]
}
```

### Alert Retrieval

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/alerts` | List alerts with optional filters |
| `GET` | `/api/v1/alerts/{id}` | Get full alert details + evidence |
| `DELETE` | `/api/v1/alerts/{id}` | Remove alert and all its chunks |

Query params: `?category=Persistence&severity=high&status=new&limit=20&offset=0`

### RAG Query

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/query` | Natural language question over all ingested data |

```json
{
  "query": "Show persistence alerts on supernova-1 involving regsvr32",
  "num_results": 5,
  "filters": { "category": "Persistence" }
}
```

Response includes the generated answer + source chunks with relevance scores.

### Summarize & Analyze

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/summarize` | Structured SOC summary of specific alerts |
| `POST` | `/api/v1/analyze` | Classify alert + compare to similar historical ones |
| `POST` | `/api/v1/analyze/categorize` | Assign MITRE ATT&CK tactic category |

### Analyze Input & Feedback (GUI workflow)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/analyze-input` | One-shot: accept raw JSON **or** free text, ingest, then analyze + summarize |
| `POST` | `/api/v1/feedback` | Record analyst approve/disapprove; disapproval reason is distilled by the LLM into a reusable lesson and stored in the `feedback` collection |
| `GET` | `/api/v1/feedback` | List stored feedback / learned knowledge |

`analyze-input` request:
```json
{ "content": "<raw Defender JSON or plain-text description>", "content_type": "auto" }
```
`content_type` is `auto` (default), `json`, or `text`. Free text is stored as a synthetic alert so feedback can reference it. Response includes `alert_id`, `input_type`, `title`, `analysis`, `summary`, `similar_alerts`.

`feedback` request:
```json
{ "alert_id": "...", "analysis": "<shown analysis>", "decision": "disapprove", "reason": "why it was wrong" }
```
On `disapprove`, the LLM synthesizes a correction that is embedded into the `feedback` collection and surfaced by future RAG queries — a closed learning loop.

### Reference Documents

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/ingest-document` | Direct text + metadata ingestion (used for STIX) |
| `POST` | `/api/v1/documents/ingest-file` | Upload a `.md` file |
| `POST` | `/api/v1/documents/ingest-directory` | Ingest all `.md` files from a directory |
| `POST` | `/api/v1/documents/load-reference` | Load built-in reference docs |
| `GET` | `/api/v1/documents` | List loaded documents |
| `DELETE` | `/api/v1/documents` | Clear all documents |

### Rules

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/rules` | List detection rules |
| `POST` | `/api/v1/rules` | Add a detection rule |

## Data Model

### Alert Chunking

Each ingested alert produces multiple chunks for granular retrieval:

| Chunk Type | Collection | Content | Metadata |
|------------|-----------|---------|----------|
| `alert_summary` | `alerts` | Title + description + category + severity | alert_id, category, severity, status, incident_id |
| `evidence_device` | `evidence` | Device name, OS, IPs, risk score | hostName, osPlatform, verdict, riskScore |
| `evidence_process` | `evidence` | Process name, command line, PID, user | processName, userAccount, verdict |
| `evidence_file` | `evidence` | File name, path, SHA256 | sha1, sha256 |

### Reference Document Chunking

Markdown documents are chunked by `##`/`###` section headings (semantic chunking, not fixed-token). Each chunk stores:
- `title` — Document title (from `#` heading or filename)
- `source` — Category (mitre-attack, lolbins, playbook, custom)
- `heading` — Section heading text
- `filename` — Source file name

### ChromaDB Collections

| Collection | Purpose | Storage |
|------------|---------|---------|
| `alerts` | Alert summary chunks | ChromaDB persistent |
| `evidence` | Device/process/file evidence chunks | ChromaDB persistent |
| `rules` | Detection rule definitions | ChromaDB persistent |
| `flags` | IOCs, indicators, patterns | ChromaDB persistent |
| `documents` | Reference docs, playbooks, STIX techniques | ChromaDB persistent |

## RAG Flow

```
User Question
     │
     ▼
1. Embed query via qwen3-embedding:0.6b (1024-dim)
     │
     ▼
2. ChromaDB similarity search across all 5 collections
     │
     ▼
3. Retrieve top-K chunks (default: 5)
     │
     ▼
4. Assemble prompt: system instruction + context chunks + question
     │
     ▼
5. Generate answer via ornith:latest (or any Ollama model)
     │
     ▼
6. Return answer + source citations + processing time
```

## Project Structure

```
alert_analyze_system/
├── app/
│   ├── main.py                 # FastAPI app, lifespan, router includes
│   ├── config.py               # Pydantic Settings from .env
│   ├── api/
│   │   ├── routes/
│   │   │   ├── ingest.py       # POST /ingest
│   │   │   ├── query.py        # POST /query
│   │   │   ├── summarize.py    # POST /summarize
│   │   │   ├── analyze.py      # POST /analyze, /analyze/categorize
│   │   │   ├── alerts.py       # GET/DELETE /alerts, /alerts/{id}
│   │   │   ├── rules.py        # GET/POST /rules
│   │   │   ├── documents.py    # Document + STIX ingestion CRUD
│   │   │   └── health.py       # GET /health, /stats
│   │   └── deps.py
│   ├── core/
│   │   ├── rag_engine.py       # Retrieval → prompt → generate
│   │   ├── embeddings.py       # Ollama embed client (batched, semaphore)
│   │   ├── llm_client.py       # Ollama LLM client (semaphore, no stream)
│   │   ├── chroma_client.py    # ChromaDB singleton wrapper
│   │   └── prompts.py          # Query, Summarize, Analyze, Categorize templates
│   ├── ingestion/
│   │   ├── parser.py           # AlertData.json → Alert objects
│   │   ├── chunker.py          # Alert → Chunk(s) with metadata
│   │   ├── ingestor.py         # Pipeline: parse → chunk → embed → store
│   │   └── document_loader.py  # Markdown → heading-chunks → embed → store
│   └── models/
│       ├── alert.py            # Alert, AlertCollection, AlertEvidence
│       ├── evidence.py         # DeviceEvidence, ProcessEvidence
│       ├── query.py            # QueryRequest, QueryResponse
│       └── rule.py             # DetectionRule
├── data/
│   ├── documents/
│   │   ├── mitre_attack/       # MITRE ATT&CK technique reference (13 files)
│   │   ├── lolbins/            # LOLBins/Signed Binary abuse reference (10 files)
│   │   └── playbooks/          # SOC playbooks, Event ID references (6 files)
│   ├── samples/                # MITRE ATT&CK STIX bundles (enterprise/ICS/mobile)
│   └── chromadb/               # ChromaDB persistent storage (gitignored)
├── tests/
│   └── test_stix_ingestion.py  # STIX bundle parsing + RAG query validation
├── client.py                   # CLI client (15+ commands)
├── AlertData.json              # Sample Microsoft Defender alert
├── .env                        # Configuration (gitignored)
├── requirements.txt
├── PLAN.md
└── README.md
```

## Embedding Model Notes

The system was tested with two embedding models. Current recommendation:

| Model | Dimensions | Speed (50 docs) | Query Quality | Verdict |
|-------|-----------|-----------------|---------------|---------|
| `nomic-embed-text:latest` | 768 | ~39 docs/sec | Good | Retired |
| **`qwen3-embedding:0.6b`** | **1024** | **~117 docs/sec** | **Better** | **Active** |

qwen3-embedding:0.6b is 3x faster and produces higher-dimensional vectors (1024 vs 768), yielding better retrieval coverage for enterprise MITRE ATT&CK queries.

## License

MIT — see [LICENSE](LICENSE).
