import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from gui import config
from gui.api_client import ApiClient
from gui.widgets.feedback_panel import FeedbackPanel
from gui.widgets.input_panel import InputPanel
from gui.widgets.result_panel import ResultPanel
from gui.workers import Worker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Alert Analyzer")
        self.resize(1100, 720)

        self.api = ApiClient(config.get_base_url())
        self._workers: list[Worker] = []
        self._current_alert_id: str = ""
        self._current_analysis: str = ""

        self.input_panel = InputPanel()
        self.result_panel = ResultPanel()
        self.feedback_panel = FeedbackPanel()

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(self.result_panel, 1)
        right_layout.addWidget(self.feedback_panel)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.input_panel)
        splitter.addWidget(right)
        splitter.setSizes([440, 660])
        self.setCentralWidget(splitter)

        self.health_label = QLabel("checking server…")
        self.statusBar().addPermanentWidget(self.health_label)
        self.statusBar().showMessage("Ready")

        self._build_menu()

        self.input_panel.analyze_requested.connect(self._on_analyze)
        self.feedback_panel.feedback_submitted.connect(self._on_feedback)

        self._refresh_health()
        self._health_timer = QTimer(self)
        self._health_timer.timeout.connect(self._refresh_health)
        self._health_timer.start(15000)

    def _build_menu(self):
        settings_menu = self.menuBar().addMenu("&Settings")
        server_action = settings_menu.addAction("Set server URL…")
        server_action.triggered.connect(self._set_server_url)

    def _set_server_url(self):
        url, ok = QInputDialog.getText(
            self, "Server URL", "Base URL:", text=config.get_base_url()
        )
        if ok and url.strip():
            config.set_base_url(url.strip())
            self.api = ApiClient(config.get_base_url())
            self._refresh_health()

    def _run(self, fn, on_success, *args, on_error=None):
        worker = Worker(fn, *args)
        worker.succeeded.connect(on_success)
        worker.failed.connect(on_error or self._on_error)
        worker.finished.connect(lambda: self._workers.remove(worker))
        self._workers.append(worker)
        worker.start()

    # ---- health ----
    def _refresh_health(self):
        self._run(self.api.health, self._on_health, on_error=self._on_health_error)

    def _on_health_error(self, _message: str):
        self.health_label.setText(
            "<span style='color:red'>● server: unreachable</span>"
        )

    def _on_health(self, data: dict):
        status = data.get("status", "unknown")
        ollama = data.get("ollama", {}).get("reachable", False)
        color = "green" if status == "healthy" else "orange"
        self.health_label.setText(
            f"<span style='color:{color}'>● server: {status} · "
            f"ollama: {'up' if ollama else 'down'}</span>"
        )

    # ---- analyze ----
    def _on_analyze(self, content: str, content_type: str):
        self.input_panel.set_enabled(False)
        self.feedback_panel.set_active(False)
        self.statusBar().showMessage("Analyzing… (this can take a while)")
        self._run(
            self.api.analyze_input,
            self._on_analyze_done,
            content,
            content_type,
        )

    def _on_analyze_done(self, result: dict):
        self.input_panel.set_enabled(True)
        self._current_alert_id = result.get("alert_id", "")
        self._current_analysis = result.get("analysis", "")
        self.result_panel.show_result(result)
        self.feedback_panel.set_active(True)
        self.statusBar().showMessage("Analysis complete — approve or disapprove.")

    # ---- feedback ----
    def _on_feedback(self, decision: str, reason: str):
        if not self._current_alert_id:
            return
        self.feedback_panel.set_active(False)
        self.statusBar().showMessage(f"Submitting {decision} feedback…")
        self._run(
            self.api.feedback,
            self._on_feedback_done,
            self._current_alert_id,
            self._current_analysis,
            decision,
            reason,
        )

    def _on_feedback_done(self, result: dict):
        decision = result.get("decision", "")
        knowledge = result.get("knowledge", "")
        if decision == "disapprove" and knowledge:
            self.result_panel.show_knowledge(knowledge)
        self.feedback_panel.reset()
        self.statusBar().showMessage(
            f"Feedback recorded ({decision}). Knowledge id: "
            f"{result.get('knowledge_id', '')}"
        )
        QMessageBox.information(
            self,
            "Feedback recorded",
            f"Decision: {decision}\n\n"
            + (knowledge if knowledge else "Thanks — your feedback was stored."),
        )

    def _on_error(self, message: str):
        self.input_panel.set_enabled(True)
        self.statusBar().showMessage("Error")
        if "server" in message.lower() or "reach" in message.lower():
            self.health_label.setText(
                "<span style='color:red'>● server: unreachable</span>"
            )
        QMessageBox.critical(self, "Error", message)

    def closeEvent(self, event):
        self._health_timer.stop()
        for worker in list(self._workers):
            worker.wait(3000)
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
