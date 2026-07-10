from PySide6.QtCore import QThread, Signal


class Worker(QThread):
    """Runs a blocking callable off the UI thread and emits the result."""

    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs

    def run(self):
        try:
            result = self._fn(*self._args, **self._kwargs)
        except Exception as e:
            self.failed.emit(str(e))
        else:
            self.succeeded.emit(result)
