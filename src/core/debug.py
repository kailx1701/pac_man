"""Ghi mốc khởi động và lỗi vào debug_trace.log."""
import faulthandler
import sys
import time
import traceback
from pathlib import Path

from src.core.config import DEBUG_TRACE

_LOG_PATH = Path(__file__).resolve().parents[2] / "debug_trace.log"
_log_file = _LOG_PATH.open("w", encoding="utf-8", buffering=1)


def trace(message):
    if DEBUG_TRACE:
        _log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {message}\n")
        _log_file.flush()


def _record_exception(label, exc_type, exc_value, exc_tb):
    formatted = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    sys.stderr.write(formatted)
    sys.stderr.flush()
    trace(f"{label}: {formatted.rstrip().replace(chr(10), ' | ')}")


def log_exception(label):
    """In và ghi lại exception hiện tại trong except."""
    _record_exception(label, *sys.exc_info())


def install_hooks(screen):
    faulthandler.enable(file=_log_file, all_threads=True)
    sys.excepthook = lambda typ, val, tb: _record_exception("sys.excepthook", typ, val, tb)

    def report_callback_exception(exc_type, exc_value, exc_tb):
        _record_exception("Tk callback", exc_type, exc_value, exc_tb)

    screen._root.report_callback_exception = report_callback_exception
    trace("exception hooks installed")
