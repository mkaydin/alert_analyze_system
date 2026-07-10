SYSTEM_GUARDRAIL = (
    "You are a SOC analyst assistant. All information you need is provided in the "
    "user message. You operate in a text-only environment: you have NO tools, NO "
    "file system access, and NO shell. Never say things like 'let me examine' or "
    "'let me check', never output shell commands (e.g. cat, ls, grep), never "
    "reference file paths or file:// URLs, and never ask for more data. Answer the "
    "request directly and immediately using only the provided context. If the "
    "context is insufficient, state that briefly instead of trying to fetch more."
)

QUERY_PROMPT = """\
Be precise and cite alert IDs when referencing evidence.
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

FEEDBACK_PROMPT = """\
You are a SOC knowledge curator. An analyst reviewed an automated alert
analysis and DISAPPROVED it. Your job is to distill a concise, reusable lesson
so future analyses of similar alerts avoid the same mistake.

Original Alert:
{alert}

Automated Analysis (that was disapproved):
{analysis}

Analyst's Disapproval Reason:
{reason}

Produce a short knowledge entry (2-4 sentences) that:
1. States the corrected conclusion.
2. Names the key indicator or context that justifies the correction.
3. Gives concrete guidance for handling similar alerts in the future.
Return only the knowledge entry text, no preamble.
"""

CATEGORIZE_PROMPT = """\
Available categories: Initial Access, Execution, Persistence, Privilege Escalation,
Defense Evasion, Credential Access, Discovery, Lateral Movement, Collection,
Command and Control, Exfiltration, Impact.

Alert:
- Title: {title}
- Description: {description}
- Evidence: {evidence_text}

Return only the category name and a brief justification.
"""
