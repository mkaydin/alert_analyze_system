from PySide6.QtWidgets import (
    QLabel,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)


class ResultPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        self.header = QLabel("<b>Analysis result</b>")
        layout.addWidget(self.header)

        self.viewer = QTextBrowser()
        self.viewer.setOpenExternalLinks(True)
        layout.addWidget(self.viewer, 1)

        self.clear()

    def clear(self):
        self.header.setText("<b>Analysis result</b>")
        self.viewer.setMarkdown(
            "_Submit an alert to see the analysis here._"
        )

    def show_result(self, result: dict):
        title = result.get("title", "") or "(untitled)"
        input_type = result.get("input_type", "")
        alert_id = result.get("alert_id", "")
        self.header.setText(
            f"<b>Analysis result</b> — {title} "
            f"<span style='color:gray'>[{input_type}] {alert_id}</span>"
        )

        parts = []
        summary = result.get("summary", "").strip()
        if summary:
            parts.append("## Summary\n\n" + summary)

        analysis = result.get("analysis", "").strip()
        if analysis:
            parts.append("## Analysis\n\n" + analysis)

        similar = result.get("similar_alerts", [])
        if similar:
            lines = ["## Similar historical alerts", ""]
            for s in similar:
                lines.append(
                    f"- `{s.get('alert_id', '')}` "
                    f"({s.get('type', '')}) — relevance {s.get('relevance', 0)}"
                )
            parts.append("\n".join(lines))

        self.viewer.setMarkdown("\n\n".join(parts) or "_No analysis returned._")

    def show_knowledge(self, knowledge: str):
        current = self.viewer.toMarkdown()
        addition = "\n\n---\n\n## Knowledge added to system\n\n" + knowledge.strip()
        self.viewer.setMarkdown(current + addition)
