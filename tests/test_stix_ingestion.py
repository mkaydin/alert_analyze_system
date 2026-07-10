"""
STIX Bundle Ingestion Test
Tests ingesting MITRE ATT&CK STIX bundles (enterprise, ICS, mobile)
into the RAG system and validates query responses.

Usage:
    # Start the server first:
    uvicorn app.main:app --port 8002 --reload

    # Run all tests:
    python tests/test_stix_ingestion.py

    # Run specific domain:
    python tests/test_stix_ingestion.py --domain enterprise

    # Run count-limited test:
    python tests/test_stix_ingestion.py --max 100
"""

import argparse
import json
import os
import sys
import time

import httpx

BASE_URL = "http://127.0.0.1:8002"
SAMPLES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "samples")

C = {
    "ok": "\033[92m",
    "warn": "\033[93m",
    "err": "\033[91m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "reset": "\033[0m",
}


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def req(method: str, path: str, **kwargs) -> httpx.Response:
    url = f"{BASE_URL}{path}"
    try:
        r = httpx.request(method, url, timeout=120, **kwargs)
        r.raise_for_status()
        return r
    except httpx.RequestError as e:
        eprint(f"  {C['err']}{e}{C['reset']}")
        sys.exit(1)
    except httpx.HTTPStatusError as e:
        body = ""
        try:
            body = e.response.text[:300]
        except Exception:
            pass
        eprint(f"  {C['err']}HTTP {e.response.status_code}: {body}{C['reset']}")
        sys.exit(1)


def health_check() -> dict:
    return req("GET", "/api/v1/health").json()


def ingest_documents(docs: list[dict]) -> dict:
    return req("POST", "/api/v1/ingest-document", json={"documents": docs}).json()


def query_rag(query_text: str, num_results: int = 5) -> dict:
    return req("POST", "/api/v1/query", json={"query": query_text, "num_results": num_results}).json()


def clear_collection(name: str):
    col_req = req("GET", "/api/v1/health").json()
    col_req  # just verifying connectivity
    req("DELETE", "/api/v1/documents")
    return True


# ─── STIX Parsing ────────────────────────────────────────────────────

STIX_VERSION_CACHE: dict[str, tuple[str, dict]] = {}


def load_stix_bundle(domain: str) -> tuple[str, dict]:
    if domain in STIX_VERSION_CACHE:
        return STIX_VERSION_CACHE[domain]

    dir_map = {"enterprise": "enterprise-attack", "ics": "ics-attack", "mobile": "mobile-attack"}
    subdir = dir_map.get(domain)
    dirpath = os.path.join(SAMPLES_DIR, subdir)
    files = sorted(f for f in os.listdir(dirpath) if f.endswith(".json"))
    latest = files[-1]
    path = os.path.join(dirpath, latest)
    with open(path) as f:
        bundle = json.load(f)
    STIX_VERSION_CACHE[domain] = (latest, bundle)
    return latest, bundle


def get_objects(bundle: dict, obj_type: str) -> list[dict]:
    return [o for o in bundle.get("objects", []) if o.get("type") == obj_type]


def technique_to_chunk(t: dict, domain_label: str) -> dict:
    name = t.get("name", "Unknown")
    refs = t.get("external_references") or []
    tid = refs[0].get("external_id", "N/A") if refs else "N/A"
    desc = (t.get("description") or "").strip()
    detection = (t.get("x_mitre_detection") or "").strip()
    platforms = ", ".join(t.get("x_mitre_platforms") or [])
    permissions = ", ".join(t.get("x_mitre_permissions_required") or [])
    tactics = [p.get("phase_name", "") for p in (t.get("kill_chain_phases") or [])]

    lines = [
        f"# {name} ({tid})",
        f"Source: {domain_label}",
        f"Platforms: {platforms}",
    ]
    if permissions:
        lines.append(f"Required Permissions: {permissions}")
    if tactics:
        lines.append(f"Tactics: {', '.join(tactics)}")
    lines.append("")

    if desc:
        lines.extend(["## Description", desc, ""])
    if detection:
        lines.extend(["## Detection", detection, ""])
    data_srcs = t.get("x_mitre_data_sources") or []
    if data_srcs:
        lines.extend(["## Data Sources", *[f"- {d}" for d in data_srcs], ""])

    return {
        "text": "\n".join(lines),
        "metadata": {
            "title": name,
            "source": f"mitre-attack-{domain_label.lower()}",
            "technique_id": tid,
            "type": "attack-pattern",
            "platforms": platforms,
            "tactics": ", ".join(tactics),
        },
    }


def domain_label(domain: str) -> str:
    return {"enterprise": "Enterprise", "ics": "ICS", "mobile": "Mobile"}.get(domain, domain)


# ─── Test Runner ─────────────────────────────────────────────────────

PASS = 0
FAIL = 0


def _run_test(name: str, passed: bool, detail: str = ""):
    global PASS, FAIL
    if passed:
        PASS += 1
        print(f"  {C['ok']}✓{C['reset']} {name}")
    else:
        FAIL += 1
        print(f"  {C['err']}✗{C['reset']} {name}")
        if detail:
            print(f"    {C['dim']}{detail[:300]}{C['reset']}")


def main():
    global BASE_URL
    parser = argparse.ArgumentParser(description="STIX Ingestion Test")
    parser.add_argument("--server", default=BASE_URL)
    parser.add_argument("--domain", choices=["enterprise", "ics", "mobile", "all"], default="all")
    parser.add_argument("--max", type=int, default=0, help="Max techniques to ingest per domain (0=all)")
    args = parser.parse_args()
    BASE_URL = args.server

    domains = ["enterprise", "ics", "mobile"] if args.domain == "all" else [args.domain]

    start_time = time.time()

    print(f"\n{C['bold']}═══ STIX Bundle Ingestion Test ═══{C['reset']}")
    print(f"{C['dim']}Server: {BASE_URL}  |  Max/domain: {'all' if not args.max else args.max}{C['reset']}\n")

    # Health
    try:
        h = health_check()
        print(f"  Server: {C['ok']}healthy{C['reset']} (up {h['uptime_seconds']}s)")
        for c in h.get("chromadb", {}).get("collections", []):
            print(f"    {c['name']}: {c['documents']} docs")
    except Exception as e:
        print(f"  {C['err']}Server unreachable: {e}{C['reset']}")
        print(f"  Start: uvicorn app.main:app --port {BASE_URL.split(':')[-1]} --reload")
        sys.exit(1)

    # ── Phase 1: Parse ─────────────────────────────────────────────
    print(f"\n{C['bold']}Phase 1: STIX Bundle Analysis{C['reset']}")

    all_techniques = []
    for domain in domains:
        version, bundle = load_stix_bundle(domain)
        techs = get_objects(bundle, "attack-pattern")
        label = domain_label(domain)
        max_t = args.max or len(techs)

        info = {
            "label": label,
            "domain": domain,
            "version": version,
            "bundle": bundle,
            "techniques": techs[:max_t],
            "stats": {
                "objects_total": len(bundle.get("objects", [])),
                "techniques": len(techs),
                "tactics": len(get_objects(bundle, "x-mitre-tactic")),
                "malware": len(get_objects(bundle, "malware")),
                "groups": len(get_objects(bundle, "intrusion-set")),
                "tools": len(get_objects(bundle, "tool")),
            },
        }
        all_techniques.append(info)

        s = info["stats"]
        print(f"\n  {C['warn']}{label} ({version}){C['reset']}")
        print(f"    Bundle: {s['objects_total']} objects, {s['techniques']} techniques{' (subset: ' + str(len(info['techniques'])) + ')' if args.max else ''}")
        print(f"    Tactics: {s['tactics']}  |  Malware: {s['malware']}  |  Groups: {s['groups']}  |  Tools: {s['tools']}")

    # ── Phase 2: Ingest ────────────────────────────────────────────
    print(f"\n{C['bold']}Phase 2: RAG Ingestion{C['reset']}")
    total_ingested = 0
    batch_size = 50

    for info in all_techniques:
        chunks = [technique_to_chunk(t, info["label"]) for t in info["techniques"]]
        print(f"  Ingesting {info['label']} ({len(chunks)} techniques)...", end=" ", flush=True)

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            ingest_documents(batch)
            total_ingested += len(batch)
            print(".", end="", flush=True)

        print(f" {total_ingested} total")

    print(f"\n  {C['ok']}Ingested: {total_ingested} technique documents{C['reset']}")

    if args.domain == "all":
        # enterprise ICS overlap ICS Enterprise = just test cross-domain query
        ics = all_techniques[1] if domains.index("ics") < len(domains) else None
        if ics:
            ics_found = get_objects(ics["bundle"], "attack-pattern")
            overlap_enterprise = [t for t in ics_found if any(
                r.get("source_name") == "mitre-attack"
                for r in (t.get("external_references") or [])
            )]
            print(f"    ICS techniques linked to Enterprise: {len(overlap_enterprise)}")

    # ── Phase 3: Query ─────────────────────────────────────────────
    print(f"\n{C['bold']}Phase 3: RAG Query Validation{C['reset']}")

    query_tests = {
        "enterprise": [
            ("Phishing initial access", "How does phishing work as an initial access technique in the MITRE ATT&CK framework?", "phishing", "spearphish"),
            ("Registry Run Keys persistence", "What are common persistence techniques using registry run keys?", "registry", "run"),
            ("Impair defenses", "How do attackers impair defenses according to MITRE ATT&CK?", "disable", "defender"),
            ("RDP lateral movement", "How is RDP used for lateral movement?", "rdp", "remote", "desktop"),
            ("LSASS credential access", "How is LSASS memory accessed for credential dumping?", "lsass", "credential"),
            ("PowerShell execution", "How is PowerShell abused for code execution?", "powershell", "script"),
            ("WMI execution", "How is WMI used for execution and lateral movement?", "wmi", "management"),
            ("Scheduled task persistence", "How are scheduled tasks used for persistence?", "task", "scheduler"),
        ],
        "ics": [
            ("ICS impact", "How do adversaries impact industrial control processes?", "process", "control"),
            ("ICS discovery", "What discovery techniques exist in ICS environments?", "device", "network"),
            ("ICS execution", "How is code executed in industrial control environments?", "command", "script"),
        ],
        "mobile": [
            ("Mobile execution", "How does execution work on mobile devices?", "user", "execution"),
            ("Mobile persistence", "How do attackers maintain access on mobile?", "boot", "startup"),
        ],
    }

    for domain in domains:
        label = domain_label(domain)
        tests = query_tests.get(domain, [])
        if not tests:
            print(f"\n  {C['dim']}No predefined queries for {label}{C['reset']}")
            continue
        print(f"\n  {C['warn']}{label} Queries:{C['reset']}")
        for qname, question, *keywords in tests:
            try:
                result = query_rag(question)
                answer = result.get("answer", "")
                sources = result.get("sources", [])
                has_kw = all(k.lower() in answer.lower() for k in keywords) if keywords else True
                has_src = len(sources) > 0
                _run_test(qname, has_kw and has_src, f"keywords: {keywords} | sources: {len(sources)}")
            except Exception as e:
                _run_test(qname, False, str(e))

    # ── Phase 4: Cross-domain ──────────────────────────────────────
    if len(domains) > 1:
        print(f"\n{C['bold']}Phase 4: Cross-Domain Queries{C['reset']}")
        cross = [
            ("Enterprise vs Mobile persistence", "Compare persistence techniques across enterprise and mobile environments"),
            ("Code execution across domains", "How does code execution differ between enterprise and industrial control environments?"),
        ]
        for qname, question in cross:
            try:
                r = query_rag(question)
                _run_test(qname, len(r.get("answer", "")) > 100, f"answer length: {len(r.get('answer', ''))}")
            except Exception as e:
                _run_test(qname, False, str(e))

    # ── Phase 5: Performance ───────────────────────────────────────
    elapsed = time.time() - start_time
    print(f"\n{C['bold']}Phase 5: Performance{C['reset']}")
    print(f"  Total time: {elapsed:.1f}s")
    print(f"  Ingestion rate: {total_ingested / elapsed:.1f} docs/sec" if elapsed > 0 else "")
    print(f"  Avg per technique: {elapsed / total_ingested:.2f}s" if total_ingested > 0 else "")

    # ── Summary ────────────────────────────────────────────────────
    total = PASS + FAIL
    print(f"\n{C['bold']}═══ Results ═══{C['reset']}")
    print(f"  {C['ok']}Passed: {PASS}{C['reset']}")
    if FAIL:
        print(f"  {C['err']}Failed: {FAIL}{C['reset']}")
    print(f"  Total:  {total}")

    # ── Improvements ───────────────────────────────────────────────
    total_techs = sum(info["stats"]["techniques"] for info in all_techniques)
    total_mal = sum(info["stats"]["malware"] for info in all_techniques)
    total_grp = sum(info["stats"]["groups"] for info in all_techniques)

    print(f"""
{C['bold']}═══ Improvements & Observations {C['reset']}
  Data Volume:
    {total_techs} attack techniques, {total_mal} malware, {total_grp} groups across {len(domains)} domain(s)

  {C['warn']}Key Recommendations:{C['reset']}
    A. Ingest malware + groups + relationships for a complete
       threat-intel graph (currently only techniques)
    B. Parse STIX relationships (21K+ objects) to build
       technique → malware → group attribution chains
    C. Extract x_mitre_detection into a dedicated chroma
       collection for detection-specific search
    D. Add a 'mitre-techniques' collection separate from
       generic 'documents' for faster technique-only queries
    E. Index STIX version deltas to track technique changes
       (e.g., new detection guidance in v19 vs v18)
    F. Create an opinionated SOC-playbook layer that maps
       techniques to Defender-specific hunting queries

  {C['dim']}Run with --max <N> to limit ingestion per domain for faster iteration.{C['reset']}
""")

    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
