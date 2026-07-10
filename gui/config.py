import os

from PySide6.QtCore import QSettings

DEFAULT_BASE_URL = os.environ.get("ALERT_GUI_BASE_URL", "http://localhost:8002")

_settings = QSettings("alert_analyze_system", "AlertAnalyzerGUI")


def get_base_url() -> str:
    return _settings.value("base_url", DEFAULT_BASE_URL, type=str)


def set_base_url(url: str) -> None:
    _settings.setValue("base_url", url.rstrip("/"))
