# Data Directory

## `chromadb/`
Persistent ChromaDB storage — vector embeddings of all ingested alerts, evidence, rules, flags, and reference documents. Auto-created on first server start. **Gitignored.**

## `samples/`
MITRE ATT&CK STIX bundles for testing and model evaluation. **Gitignored** (too large for GitHub).

Download from the official MITRE ATT&CK STIX data repository:

```bash
# Clone the full ATT&CK STIX data (all versions, all domains)
git clone https://github.com/mitre-attack/attack-stix-data.git /tmp/attack-stix-data

# Copy the latest versions into data/samples/
cp -r /tmp/attack-stix-data/enterprise-attack   data/samples/enterprise-attack
cp -r /tmp/attack-stix-data/ics-attack          data/samples/ics-attack
cp -r /tmp/attack-stix-data/mobile-attack       data/samples/mobile-attack
```

Or download individual bundle files directly:

- **Enterprise ATT&CK:** https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack.json
- **ICS ATT&CK:** https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/ics-attack/ics-attack.json
- **Mobile ATT&CK:** https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/mobile-attack/mobile-attack.json

### Expected Contents

| Directory | Files | Objects | Techniques |
|-----------|-------|---------|------------|
| `enterprise-attack/` | Version history (1.0–19.1) + latest `enterprise-attack.json` | ~25,800 | ~858 |
| `ics-attack/` | Version history + latest `ics-attack.json` | ~2,200 | ~118 |
| `mobile-attack/` | Version history + latest `mobile-attack.json` | ~2,600 | ~190 |

### Usage

```bash
# Run the STIX ingestion test
python tests/test_stix_ingestion.py
```

## `documents/`
Reference documents ingested into the RAG system as searchable knowledge. These **are** tracked in git:

- `documents/mitre_attack/` — MITRE ATT&CK technique reference guides
- `documents/lolbins/` — Living Off the Land Binaries cheat sheets
- `documents/playbooks/` — SOC investigation playbooks

To load: `python client.py doc-load-ref` or `python client.py doc-load data/documents`
