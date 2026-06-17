"""
SQL executor — runs validated read-only queries and returns tabular results.
"""

from typing import Any

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from src.utils.logger import setup_logger

logger = setup_logger("nl2sql_executor")

_QUERY_TIMEOUT_SECONDS = 5


def execute_sql(engine: Engine, sql: str) -> dict[str, Any]:
    """Execute a validated SELECT query and return structured results."""
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(sql), con=conn)
    except Exception as e:
        logger.error(f"SQL execution failed: {e}")
        raise RuntimeError(f"Query execution failed: {e}") from e

    columns = [str(c) for c in df.columns.tolist()]
    rows: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        record: dict[str, Any] = {}
        for col in columns:
            val = row[col]
            if hasattr(val, "isoformat"):
                record[col] = val.isoformat()
            elif pd.isna(val):
                record[col] = None
            elif hasattr(val, "item"):
                record[col] = val.item()
            else:
                record[col] = val
        rows.append(record)

    truncated = len(rows) >= 100
    return {
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
        "truncated": truncated,
    }
