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

CATEGORIZE_PROMPT = """\
System: You are a SOC analyst. Categorize the following security alert into
the most appropriate MITRE ATT&CK tactic category. Consider the alert title,
description, and evidence.

Available categories: Initial Access, Execution, Persistence, Privilege Escalation,
Defense Evasion, Credential Access, Discovery, Lateral Movement, Collection,
Command and Control, Exfiltration, Impact.

Alert:
- Title: {title}
- Description: {description}
- Evidence: {evidence_text}

Return only the category name and a brief justification.
"""
