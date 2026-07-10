from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class InputPanel(QWidget):
    analyze_requested = Signal(str, str)  # content, content_type

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("<b>Alert input</b> — paste JSON or plain text"))

        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText(
            "Paste a Microsoft Defender alert JSON, or describe an alert in plain text..."
        )
        layout.addWidget(self.editor, 1)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["auto", "json", "text"])
        controls.addWidget(self.type_combo)

        self.load_btn = QPushButton("Load JSON file…")
        self.load_btn.clicked.connect(self._load_file)
        controls.addWidget(self.load_btn)

        controls.addStretch(1)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.editor.clear)
        controls.addWidget(self.clear_btn)

        self.analyze_btn = QPushButton("Analyze")
        self.analyze_btn.setDefault(True)
        self.analyze_btn.clicked.connect(self._emit_analyze)
        controls.addWidget(self.analyze_btn)

        layout.addLayout(controls)

    def _load_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open alert JSON", "", "JSON files (*.json);;All files (*)"
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.editor.setPlainText(f.read())
                self.type_combo.setCurrentText("json")
            except OSError as e:
                self.editor.setPlainText(f"[Failed to read file: {e}]")

    def _emit_analyze(self):
        content = self.editor.toPlainText().strip()
        if not content:
            return
        self.analyze_requested.emit(content, self.type_combo.currentText())

    def set_enabled(self, enabled: bool):
        self.analyze_btn.setEnabled(enabled)
        self.load_btn.setEnabled(enabled)
        self.editor.setReadOnly(not enabled)
