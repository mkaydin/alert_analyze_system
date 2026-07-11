# High-Level Implementation Plan for Alert Analysis RAG System

## Overview
This project is a fully-local Retrieval-Augmented Generation (RAG) system for analyzing Microsoft Defender security alerts. The system ingests Defender alert JSON, chunks and embeds evidence into ChromaDB, then answers natural language questions via Ollama — all offline, no cloud APIs.

## Technology Stack

### Backend
- **Python 3.12+** - Main programming language
- **FastAPI** - Web framework for REST API
- **ChromaDB** - Vector database for embeddings
- **Ollama** - Local LLM and embedding models (qwen3-embedding:0.6b, ornith:latest)
- **httpx** - Async HTTP client for Ollama API calls
- **pydantic-settings** - Configuration management via .env files

### Frontend
- **PySide6** - Cross-platform GUI framework (Linux, macOS, Windows)
- **Markdown rendering** - For displaying analysis results

### Infrastructure
- **Docker** - Containerization for consistent deployment
- **Docker Compose** - Multi-service orchestration
- **GitHub Actions** - CI/CD pipeline (to be implemented)

## System Architecture

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
               │  ┌──────┬────────┴──────┬──────┬──────┬────┐ │
               │  │alerts│evidence│ rules│flags │doc │ │
               │  └──────┴────────┴──────┴──────┴──────┴────┘ │
               └───────────────────────────────────────┘
```

## Key Features

### Alert Ingestion
- Parse Microsoft Defender `AlertData.json`
- Chunk by alert summary + per-evidence entry
- Embed and store in ChromaDB
- Support for both single alerts and batch ingestion

### Natural Language Query
- Ask questions about threats, processes, devices, IOCs
- RAG retrieves relevant chunks from 5 collections
- Generates answers via local LLM
- Includes source citations and relevance scores

### Summarization
- Generate SOC-report-style summaries (concise, detailed, or soc-report format)
- Extract key findings, affected assets, and MITRE ATT&CK mappings
- Provide actionable recommendations

### Alert Analysis & Categorization
- Classify alerts (TP/FP/Suspicious/Needs Review)
- Compare against similar historical alerts
- Assign MITRE ATT&CK tactics with confidence scores
- Provide priority adjustments and next steps

### Reference Document Ingestion
- Load MITRE ATT&CK guides, LOLBins playbooks, SOC response procedures as searchable markdown documents
- Semantic chunking by headings (##, ###)

### CLI Client
- 15+ commands: `ingest`, `query`, `summarize`, `analyze`, `categorize`, `alerts`, `rules`, `health`, `stats`, `doc-load`, `doc-list`, and more

### STIX Bundle Ingestion
- Bulk-ingest MITRE ATT&CK enterprise/ICS/mobile technique data (850+ techniques)
- Pre-built test suite for validation

### Concurrency Control
- Independent semaphores for embedding and LLM calls prevent Ollama overload
- Batched embedding to optimize Ollama throughput
- Request queuing during high load

## Data Model

### Alert Chunking
Each ingested alert produces multiple chunks for granular retrieval:

| Chunk Type | Collection | Content | Metadata |
|------------|-----------|----------|----------|
| `alert_summary` | `alerts` | Title + description + category + severity | alert_id, category, severity, status, incident_id |
| `evidence_device` | `evidence` | Device name, OS, IPs, risk score, verdict | hostName, osPlatform, verdict, riskScore |
| `evidence_process` | `evidence` | Process name, command line, PID, user, verdict | processName, userAccount, verdict, parentProcessId |
| `evidence_file` | `evidence` | File name, path, SHA256, verdict | sha1, sha256, filePath |

### Reference Document Chunking
Markdown documents are chunked by `##`/`###` section headings (semantic chunking, not fixed-token). Each chunk stores:
- `title` — Document title (from `#` heading or filename)
- `source` — Category (mitre-attack, lolbins, playbook, custom)
- `heading` — Section heading text
- `filename` — Source file name

## Configuration

### Environment Variables (.env)
```
# Ollama Connection
ALERT_OLLAMA_HOST=http://localhost:11434
ALERT_EMBED_MODEL=qwen3-embedding:0.6b
ALERT_LLM_MODEL=ornith:latest
ALERT_OLLAMA_CONCURRENCY=4
ALERT_OLLAMA_TIMEOUT=60
ALERT_LLM_TEMPERATURE=0.1
ALERT_LLM_MAX_TOKENS=2048

# ChromaDB Storage
ALERT_CHROMADB_PATH=data/chromadb
ALERT_CHROMADB_COLLECTIONS=alerts,evidence,rules,flags,documents,feedback

# Server Configuration
ALERT_HOST=0.0.0.0
ALERT_PORT=8002
ALERT_RELOAD=true

# CORS Settings
CORS_ORIGINS=*
CORS_CREDENTIALS=true
CORS_METHODS=GET,POST,PUT,DELETE,OPTIONS

# Rate Limiting
ALERT_RATE_LIMIT=1000
ALERT_RATE_WINDOW=60
```

### Docker Configuration
docker-compose.yml manages all services:
- Ollama for embeddings and LLM
- ChromaDB for persistent vector storage
- FastAPI backend
- GUI client with reverse proxy

## Deployment

### Prerequisites
```bash
# Required models (pull from Ollama)
ollama pull qwen3-embedding:0.6b
ollama pull ornith:latest

# Install dependencies
pip install -r requirements.txt
pip install -r gui/requirements-gui.txt

# Configure environment
cp .env.example .env

# Start the stack
docker-compose up --build
```

### Access the System
- **API:** `http://localhost:8002`
- **GUI:** `http://localhost:8080`
- **Health Check:** `curl http://localhost:8002/api/v1/health`

### Production Deployment
1. **Docker Hub / GitHub Packages**: Push images to container registry
2. **Kubernetes**: Use Helm charts for orchestration
3. **Systemd Services**: Create init scripts for systemd
4. **Monitoring**: Setup Prometheus/Grafana for metrics
5. **Backup**: Regular backups of ChromaDB data directory

## Development Workflow

### Local Development
```bash
# Start Ollama first
ollama serve

# Start FastAPI server in background
uvicorn app.main:app --reload --port 8002

# Start GUI client
python -m gui.app
```

### Testing
- **Unit Tests**: pytest for individual modules
- **Integration Tests**: Test full API flows
- **E2E Tests**: GUI interaction tests
- **Load Tests**: Simulate production traffic

### Code Quality
- **linting**: ruff for Python code style
- **type hints**: pyright for type checking
- **documentation**: auto-generated API docs
- **pre-commit**: GitHub Actions for CI/CD

## Security Considerations

### Local Security
- Network isolation using Docker networks
- Read-only filesystem for sensitive data
- Container security with non-root users
- TLS/SSL for external communications

### Data Security
- All processing happens locally
- No data leaves the local machine
- Encryption at rest for sensitive information
- Audit logging for all operations

### Compliance
- GDPR compliance for EU users
- HIPAA considerations for healthcare data
- SOC 2 Type II for security controls

## Performance Optimization

### LLM Optimization
- **Batching**: Group multiple requests for efficiency
- **Caching**: Cache frequent LLM responses
- **Model selection**: Choose appropriate model size based on query complexity

### Database Optimization
- **Indexing**: Proper index creation for fast lookups
- **Partitioning**: Split large collections for better performance
- **Query optimization**: Refine queries for minimal scan overhead

### System Resources
- **Resource limits**: Configure CPU/memory limits for containers
- **Monitoring**: Track resource usage for capacity planning
- **Autoscaling**: Scale horizontally based on load

## Maintenance

### Regular Tasks
- **Backup**: Weekly backups of ChromaDB data
- **Log rotation**: Manage log file sizes
- **Security updates**: Patch system packages
- **Model updates**: Update Ollama models as needed

### Troubleshooting
- **Health checks**: Monitor system health via API endpoints
- **Logging**: Enable debug logging for troubleshooting
- **Support**: Implement support tickets and escalation procedures

## Future Enhancements

### Advanced Features
1. **Multi-modal support**: Image and file analysis
2. **Knowledge graphs**: Enhanced relationship modeling
3. **Fine-tuning**: Custom model training on domain data
4. **Real-time streaming**: Continuous alert processing

### Integration Options
1. **Siem integration**: Forward findings to SIEM systems
2. **Threat intelligence**: Integrate with threat feeds
3. **Automation**: Playbook automation based on findings
4. **Reporting**: Generate compliance reports

## Conclusion

This Alert Analysis RAG System provides a powerful, local solution for security alert analysis. The combination of Ollama's local LLMs, ChromaDB's vector search, and a comprehensive GUI makes complex security analysis accessible to SOC analysts and security teams of all sizes.

The system is designed with scalability, security, and ease of use in mind, making it suitable for both development and production environments. The Docker-based deployment ensures consistent behavior across all environments.

---

**Key Benefits:**
- ✅ **100% Local** - No external API calls
- ✅ **Offline**: Works disconnected
- ✅ **Scalable** - Docker containerization enables horizontal scaling
- ✅ **Secure**: Local processing, no data leakage
- ✅ **Flexible**: Supports both CLI and GUI interfaces
- ✅ **Extensible**: Easy to add new alert types and analysis modules
- ✅ **Performant**: Optimized for enterprise-scale workloads

**Security**: All sensitive processing occurs locally
**Compliance**: Designed for GDPR, HIPAA, and SOC 2 compliance
**Cost-effective**: Utilizes existing local infrastructure efficiently