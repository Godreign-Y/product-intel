"""
Relative date resolution anchored to the latest date in the dataset.

The dataset is historical (ends 2025-12-31), so phrases like "last week" must
be interpreted relative to the most recent data date, NOT the real-world clock.
This avoids both crashes (pd.to_datetime cannot parse "last week") and empty
results (filtering on a future calendar date).
"""

import re
from datetime import timedelta
from typing import Any, Optional

import pandas as pd

from src.utils.logger import setup_logger

logger = setup_logger("nl2sql_dates")

_cached_reference: Optional[pd.Timestamp] = None


def get_reference_date(force_refresh: bool = False) -> pd.Timestamp:
    """Return the latest date available in the data (cached)."""
    global _cached_reference
    if _cached_reference is not None and not force_refresh:
        return _cached_reference
    try:
        from src.api.dependencies import get_max_date_from_db
        _cached_reference = pd.to_datetime(get_max_date_from_db())
    except Exception as e:
        logger.warning(f"Could not resolve reference date from DB: {e}")
        _cached_reference = pd.Timestamp.now().normalize()
    return _cached_reference


def resolve_date(value: Any, reference: Optional[pd.Timestamp] = None) -> Optional[pd.Timestamp]:
    """
    Convert an absolute or relative date expression to a Timestamp.

    Returns None for unparseable input (caller should then skip the filter).
    """
    if value is None or value == "":
        return None
    if isinstance(value, pd.Timestamp):
        return value
    if hasattr(value, "strftime") and not isinstance(value, str):
        return pd.to_datetime(value)

    text = str(value).strip().lower()
    if not text or text in {"null", "none", "any", "all"}:
        return None

    ref = reference or get_reference_date()

    if text in {"today", "now", "current", "latest"}:
        return ref
    if text == "yesterday":
        return ref - timedelta(days=1)
    if any(p in text for p in ("past week", "last week", "this week", "past 7 days", "last 7 days")):
        return ref - timedelta(days=6)
    if any(p in text for p in ("past month", "last month", "this month", "past 30 days", "last 30 days")):
        return ref - timedelta(days=29)
    if any(p in text for p in ("past quarter", "last quarter", "past 90 days", "last 90 days")):
        return ref - timedelta(days=89)
    if any(p in text for p in ("past year", "last year", "this year")):
        return ref - timedelta(days=364)

    m = re.match(r"^(\d+)\s*days?\s*ago$", text)
    if m:
        return ref - timedelta(days=int(m.group(1)))
    m = re.match(r"^(\d+)\s*weeks?\s*ago$", text)
    if m:
        return ref - timedelta(weeks=int(m.group(1)))
    m = re.match(r"^(\d+)\s*months?\s*ago$", text)
    if m:
        return ref - timedelta(days=30 * int(m.group(1)))

    try:
        return pd.to_datetime(text)
    except Exception:
        logger.info(f"Unparseable date expression ignored: '{value}'")
        return None


def safe_parse_date(value: Any) -> Optional[pd.Timestamp]:
    """Parse a date param without ever raising. Returns None if unparseable."""
    try:
        return resolve_date(value)
    except Exception:
        return None


def get_date_context_for_prompt() -> str:
    """Anchor text so the LLM maps relative phrases to the data's date range."""
    try:
        ref = get_reference_date()
        week_start = (ref - timedelta(days=6)).strftime("%Y-%m-%d")
        month_start = (ref - timedelta(days=29)).strftime("%Y-%m-%d")
        ref_str = ref.strftime("%Y-%m-%d")
        return (
            "IMPORTANT DATE CONTEXT (the data is historical):\n"
            f"- The most recent date in the data is {ref_str}. Treat this as 'today'.\n"
            f"- 'last week' / 'past week' / 'last 7 days' => date >= '{week_start}' AND date <= '{ref_str}'\n"
            f"- 'last month' / 'past month' => date >= '{month_start}' AND date <= '{ref_str}'\n"
            "- NEVER filter on the real-world calendar date; only use dates within the data range."
        )
    except Exception:
        return ""
