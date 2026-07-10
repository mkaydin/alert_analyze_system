"""
CLI client for Alert Analysis RAG System.

Usage:
  # Ingest alert data
  python client.py ingest AlertData.json

  # Query using natural language
  python client.py query "What persistence mechanisms were detected?"

  # Summarize an alert
  python client.py summarize <alert_id> [--format concise|soc-report|detailed]

  # Analyze an alert (with similar historical comparison)
  python client.py analyze <alert_id> [--no-similar]

  # Categorize an alert
  python client.py categorize <alert_id>

  # List all ingested alerts
  python client.py alerts [--category Persistence] [--severity high] [--limit 20]

  # Show alert details
  python client.py get-alert <alert_id>

  # Delete an alert
  python client.py delete-alert <alert_id>

  # Manage rules
  python client.py rules
  python client.py add-rule '{"name":"...", "category":"...", "severity":"high"}'

  # Health check
  python client.py health

  # Stats
  python client.py stats

  # Full pipeline: ingest a file, then ask a question about it
  python client.py analyze-file AlertData.json "What threats were found?"
"""

import argparse
import json
import os
import sys
import time

import httpx

BASE_URL = os.environ.get("ALERT_GUI_BASE_URL", "http://127.0.0.1:8002")

COLOR_OK = "\033[92m"
COLOR_WARN = "\033[93m"
COLOR_ERR = "\033[91m"
COLOR_BOLD = "\033[1m"
COLOR_DIM = "\033[2m"
COLOR_RESET = "\033[0m"


def _req(method: str, path: str, **kwargs) -> httpx.Response:
    url = f"{BASE_URL}{path}"
    try:
        r = httpx.request(method, url, timeout=120, **kwargs)
        r.raise_for_status()
        return r
    except httpx.RequestError as e:
        print(f"{COLOR_ERR}Connection error: {e}{COLOR_RESET}", file=sys.stderr)
        sys.exit(1)
    except httpx.HTTPStatusError as e:
        body = ""
        try:
            body = e.response.text
        except Exception:
            pass
        print(
            f"{COLOR_ERR}HTTP {e.response.status_code}: {body}{COLOR_RESET}",
            file=sys.stderr,
        )
        sys.exit(1)


def cmd_health(args=None):
    r = _req("GET", "/api/v1/health")
    data = r.json()
    status = data["status"]
    color = COLOR_OK if status == "healthy" else COLOR_WARN
    print(f"\n{COLOR_BOLD}System Health:{COLOR_RESET}  {color}{status}{COLOR_RESET}")
    print(f"  Uptime: {data['uptime_seconds']}s")
    ollama = data["ollama"]
    print(f"\n  Ollama: {'✓' if ollama['reachable'] else '✗'}")
    if ollama["models"]:
        for m in ollama["models"]:
            print(f"    - {m}")
    print(f"  Concurrency: {ollama['concurrency']}")
    cb = data["chromadb"]
    print(f"\n  ChromaDB: {'✓' if cb['status'] == 'connected' else '✗'}")
    for c in cb.get("collections", []):
        print(f"    - {c['name']}: {c['documents']} documents")
    print()


def cmd_stats(args=None):
    r = _req("GET", "/api/v1/stats")
    print(json.dumps(r.json(), indent=2))


def cmd_ingest(args):
    path = args.file
    with open(path) as f:
        payload = json.load(f)
    print(f"{COLOR_DIM}Ingesting {path}...{COLOR_RESET}")
    r = _req("POST", "/api/v1/ingest", json=payload)
    result = r.json()
    print(
        f"{COLOR_OK}Ingested {result['ingested']} alert(s), "
        f"{result['chunks_created']} chunk(s) created{COLOR_RESET}"
    )
    for aid in result.get("alert_ids", []):
        print(f"  - {aid}")
    return result.get("alert_ids", [])


def cmd_query(args):
    r = _req(
        "POST",
        "/api/v1/query",
        json={
            "query": args.query,
            "num_results": args.num_results,
            "filters": json.loads(args.filters) if args.filters else None,
        },
    )
    data = r.json()
    print(f"\n{COLOR_BOLD}Answer:{COLOR_RESET}\n{data['answer']}")
    if data.get("sources"):
        print(f"\n{COLOR_DIM}Sources ({len(data['sources'])}):{COLOR_RESET}")
        for s in data["sources"]:
            print(
                f"  [{s['type']}] alert={s['alert_id'][:16]}... "
                f"relevance={s['relevance']}"
            )
    print(f"\n{COLOR_DIM}Processing time: {data['processing_time_ms']}ms{COLOR_RESET}\n")


def cmd_summarize(args):
    r = _req(
        "POST",
        "/api/v1/summarize",
        json={"alert_ids": args.alert_ids, "format": args.format},
    )
    data = r.json()
    for s in data.get("summaries", []):
        aid = s.get("alert_id", "?")
        if "error" in s:
            print(f"{COLOR_ERR}[{aid}] Error: {s['error']}{COLOR_RESET}")
        else:
            print(f"\n{COLOR_BOLD}Summary for {aid}:{COLOR_RESET}")
            print(s.get("summary", ""))


def cmd_analyze(args):
    r = _req(
        "POST",
        "/api/v1/analyze",
        json={
            "alert_id": args.alert_id,
            "include_similar": not args.no_similar,
        },
    )
    data = r.json()
    print(f"\n{COLOR_BOLD}Analysis for {data['alert_id']}:{COLOR_RESET}")
    print(data.get("analysis", ""))
    if data.get("similar_alerts"):
        print(f"\n{COLOR_DIM}Similar alerts:{COLOR_RESET}")
        for s in data["similar_alerts"]:
            print(f"  - {s.get('alert_id', '?')} (relevance: {s.get('relevance', 0)})")


def cmd_categorize(args):
    r = _req(
        "POST",
        "/api/v1/analyze/categorize",
        json={"alert_id": args.alert_id},
    )
    data = r.json()
    print(f"\n{COLOR_BOLD}Category for {data['alert_id']}:{COLOR_RESET}")
    print(data.get("category_assignment", ""))


def cmd_alerts(args):
    params = {}
    if args.category:
        params["category"] = args.category
    if args.severity:
        params["severity"] = args.severity
    if args.status:
        params["status"] = args.status
    params["limit"] = str(args.limit)
    params["offset"] = str(args.offset)

    r = _req("GET", "/api/v1/alerts", params=params)
    data = r.json()
    print(f"\n{COLOR_BOLD}Alerts ({data['total']} total, showing {data['limit']}):{COLOR_RESET}")
    for a in data.get("alerts", []):
        print(
            f"  {a['id'][:24]}  "
            f"{COLOR_WARN}{a['severity']:>14}{COLOR_RESET}  "
            f"{a['category']:>20}  "
            f"{a['status']:>12}  "
            f"{a['title'][:50]}"
        )
    print()


def cmd_get_alert(args):
    r = _req("GET", f"/api/v1/alerts/{args.alert_id}")
    data = r.json()
    print(f"\n{COLOR_BOLD}Alert: {data['id']}{COLOR_RESET}")
    meta = data.get("metadata", {})
    for k, v in meta.items():
        print(f"  {k}: {v}")
    print(f"\n  Summary: {data.get('summary', '')[:200]}")
    print(f"\n  Evidence count: {data.get('evidence_count', 0)}")
    for ev in data.get("evidence", [])[:3]:
        print(f"    - {ev.get('text', '')[:100]}")


def cmd_delete_alert(args):
    r = _req("DELETE", f"/api/v1/alerts/{args.alert_id}")
    data = r.json()
    print(
        f"{COLOR_OK}Deleted {data['alert_id']} "
        f"({data['chunks_removed']} chunks removed){COLOR_RESET}"
    )


def cmd_rules():
    r = _req("GET", "/api/v1/rules")
    data = r.json()
    print(f"\n{COLOR_BOLD}Detection Rules ({data['total']}):{COLOR_RESET}")
    for rule in data.get("rules", []):
        print(f"  [{rule['id'][:12]}] {rule['name']}  "
              f"{COLOR_WARN}{rule['severity']}{COLOR_RESET}  "
              f"{rule['category']}")
    print()


def cmd_add_rule(args):
    rule = json.loads(args.json)
    r = _req("POST", "/api/v1/rules", json=rule)
    data = r.json()
    print(f"{COLOR_OK}Rule created: {data['name']} ({data['id']}){COLOR_RESET}")


def cmd_doc_load(args):
    r = _req("POST", "/api/v1/documents/ingest-directory", json={"path": args.path})
    data = r.json()
    print(f"{COLOR_OK}Loaded {data['total']} document(s) from {args.path}{COLOR_RESET}")
    for res in data.get("results", []):
        print(f"  - {res['file']}: {res['chunks_created']} chunks ({res['source']})")


def cmd_doc_load_ref(args=None):
    r = _req("POST", "/api/v1/documents/load-reference")
    data = r.json()
    print(f"{COLOR_OK}Loaded reference documents{COLOR_RESET}")
    for res in data.get("results", []):
        print(f"  - {res['file']}: {res['chunks_created']} chunks ({res['source']})")
    print(f"{COLOR_BOLD}Total chunks: {data['total_chunks']}{COLOR_RESET}")


def cmd_doc_list(args=None):
    r = _req("GET", "/api/v1/documents")
    data = r.json()
    docs = data.get("documents", [])
    print(f"\n{COLOR_BOLD}Reference Documents ({len(docs)}):{COLOR_RESET}")
    sources = {}
    for d in docs:
        s = d.get("source", "unknown")
        sources.setdefault(s, []).append(d["title"])
    for src, titles in sorted(sources.items()):
        print(f"\n  {COLOR_WARN}{src}{COLOR_RESET}")
        for t in titles:
            print(f"    - {t}")
    print()


def cmd_analyze_file(args):
    alert_ids = cmd_ingest(args)
    if not alert_ids:
        print(f"{COLOR_ERR}No alerts ingested, nothing to query.{COLOR_RESET}")
        return

    print(f"\n{COLOR_BOLD}--- Querying: {args.question} ---{COLOR_RESET}")
    query_args = argparse.Namespace(
        query=args.question,
        num_results=5,
        filters=None,
    )
    cmd_query(query_args)

    if args.summarize:
        print(f"\n{COLOR_BOLD}--- Summarizing ingested alerts ---{COLOR_RESET}")
        summ_args = argparse.Namespace(
            alert_ids=alert_ids,
            format="concise",
        )
        cmd_summarize(summ_args)


def main():
    global BASE_URL
    parser = argparse.ArgumentParser(
        description="Alert Analysis RAG System — CLI Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--server",
        default=None,
        help=f"Server URL (default: {BASE_URL})",
    )

    sub = parser.add_subparsers(dest="command")

    p_health = sub.add_parser("health", help="Check server health")
    p_stats = sub.add_parser("stats", help="Show collection stats")

    p_ingest = sub.add_parser("ingest", help="Ingest alert JSON file")
    p_ingest.add_argument("file", help="Path to AlertData.json")

    p_query = sub.add_parser("query", help="Natural language query")
    p_query.add_argument("query", help="Question about alerts")
    p_query.add_argument("--num-results", type=int, default=5)
    p_query.add_argument("--filters", help='JSON filter, e.g. \'{"category":"Persistence"}\'')

    p_summ = sub.add_parser("summarize", help="Summarize alerts")
    p_summ.add_argument("alert_ids", nargs="+", help="Alert ID(s)")
    p_summ.add_argument("--format", default="concise",
                        choices=["concise", "detailed", "soc-report"])

    p_anal = sub.add_parser("analyze", help="Analyze an alert")
    p_anal.add_argument("alert_id", help="Alert ID")
    p_anal.add_argument("--no-similar", action="store_true",
                        help="Skip similar alert comparison")

    p_cat = sub.add_parser("categorize", help="Categorize an alert (MITRE ATT&CK)")
    p_cat.add_argument("alert_id", help="Alert ID")

    p_alerts = sub.add_parser("alerts", help="List ingested alerts")
    p_alerts.add_argument("--category")
    p_alerts.add_argument("--severity")
    p_alerts.add_argument("--status")
    p_alerts.add_argument("--limit", type=int, default=20)
    p_alerts.add_argument("--offset", type=int, default=0)

    p_get = sub.add_parser("get-alert", help="Show alert details")
    p_get.add_argument("alert_id")

    p_del = sub.add_parser("delete-alert", help="Delete an alert")
    p_del.add_argument("alert_id")

    p_rules = sub.add_parser("rules", help="List detection rules")
    p_add = sub.add_parser("add-rule", help="Add a detection rule")
    p_add.add_argument("json", help='Rule JSON: \'{"name":"...","category":"..."}\'')

    p_af = sub.add_parser(
        "analyze-file",
        help="Full pipeline: ingest file + query + optional summarize"
    )
    p_af.add_argument("file", help="Path to AlertData.json")
    p_af.add_argument("question", help="Natural language question")
    p_af.add_argument("--summarize", action="store_true",
                      help="Also summarize ingested alerts")

    # --- Document commands ---
    p_doc_load = sub.add_parser("doc-load", help="Load reference documents from directory")
    p_doc_load.add_argument("path", nargs="?",
                            default="data/documents",
                            help="Directory with .md files (default: data/documents)")

    p_doc_load_ref = sub.add_parser("doc-load-ref", help="Load built-in reference documents (MITRE, LOLBins, playbooks)")

    p_doc_list = sub.add_parser("doc-list", help="List loaded reference documents")

    args = parser.parse_args()

    if args.server:
        BASE_URL = args.server

    handlers = {
        "health": cmd_health,
        "stats": cmd_stats,
        "ingest": cmd_ingest,
        "query": cmd_query,
        "summarize": cmd_summarize,
        "analyze": cmd_analyze,
        "categorize": cmd_categorize,
        "alerts": cmd_alerts,
        "get-alert": cmd_get_alert,
        "delete-alert": cmd_delete_alert,
        "rules": cmd_rules,
        "add-rule": cmd_add_rule,
        "analyze-file": cmd_analyze_file,
        "doc-load": cmd_doc_load,
        "doc-load-ref": cmd_doc_load_ref,
        "doc-list": cmd_doc_list,
    }

    handler = handlers.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
