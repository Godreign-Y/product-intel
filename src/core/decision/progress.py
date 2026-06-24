"""Thread-safe progress events for streaming decision_ask to the UI."""

from __future__ import annotations

import threading
from typing import Any, Callable, Dict, List, Optional

_emitter: Optional[Callable[[Dict[str, Any]], None]] = None
_lock = threading.Lock()
_buffer: List[Dict[str, Any]] = []


def set_progress_emitter(emitter: Optional[Callable[[Dict[str, Any]], None]]) -> None:
    global _emitter
    with _lock:
        _emitter = emitter


def emit_progress(event: Dict[str, Any]) -> None:
    with _lock:
        if _emitter is not None:
            try:
                _emitter(event)
            except Exception:
                pass
        else:
            _buffer.append(event)


def drain_buffered_events() -> List[Dict[str, Any]]:
    with _lock:
        events = list(_buffer)
        _buffer.clear()
        return events


def clear_progress_buffer() -> None:
    with _lock:
        _buffer.clear()
