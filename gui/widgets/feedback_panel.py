from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class FeedbackPanel(QWidget):
    # decision, reason
    feedback_submitted = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        buttons = QHBoxLayout()
        self.approve_btn = QPushButton("Approve")
        self.approve_btn.clicked.connect(self._on_approve)
        buttons.addWidget(self.approve_btn)

        self.disapprove_btn = QPushButton("Disapprove")
        self.disapprove_btn.clicked.connect(self._on_disapprove)
        buttons.addWidget(self.disapprove_btn)
        buttons.addStretch(1)
        layout.addLayout(buttons)

        self.reason_label = QLabel("Reason for disapproval (sent to AI to learn from):")
        self.reason_edit = QPlainTextEdit()
        self.reason_edit.setPlaceholderText(
            "Explain what the analysis got wrong and the correct conclusion..."
        )
        self.reason_edit.setFixedHeight(90)

        submit_row = QHBoxLayout()
        submit_row.addStretch(1)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self._hide_reason)
        self.submit_btn = QPushButton("Submit feedback")
        self.submit_btn.clicked.connect(self._on_submit_reason)
        submit_row.addWidget(self.cancel_btn)
        submit_row.addWidget(self.submit_btn)

        layout.addWidget(self.reason_label)
        layout.addWidget(self.reason_edit)
        layout.addLayout(submit_row)

        self.set_active(False)
        self._hide_reason()

    def set_active(self, active: bool):
        """Enable the approve/disapprove buttons once a result exists."""
        self.approve_btn.setEnabled(active)
        self.disapprove_btn.setEnabled(active)
        if not active:
            self._hide_reason()

    def _show_reason(self):
        self.reason_label.setVisible(True)
        self.reason_edit.setVisible(True)
        self.cancel_btn.setVisible(True)
        self.submit_btn.setVisible(True)
        self.reason_edit.setFocus()

    def _hide_reason(self):
        self.reason_label.setVisible(False)
        self.reason_edit.setVisible(False)
        self.cancel_btn.setVisible(False)
        self.submit_btn.setVisible(False)

    def _on_approve(self):
        self.feedback_submitted.emit("approve", "")

    def _on_disapprove(self):
        self._show_reason()

    def _on_submit_reason(self):
        reason = self.reason_edit.toPlainText().strip()
        if not reason:
            self.reason_edit.setPlaceholderText("A reason is required to disapprove.")
            return
        self.feedback_submitted.emit("disapprove", reason)

    def reset(self):
        self.reason_edit.clear()
        self.set_active(False)
