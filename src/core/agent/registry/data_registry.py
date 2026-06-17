"""
Data Registry — provides the planner with knowledge of available data.

Dynamically queries the database/CSV to report available products,
categories, date ranges, metrics, and driver columns.
"""

import os
from typing import Any

import pandas as pd

from src.core.nl2sql.schema import ALLOWED_TABLES, TABLE_SCHEMAS
from src.utils.logger import setup_logger

logger = setup_logger("data_registry")

# Static schema knowledge
METRICS = ["revenue", "profit", "orders", "conversion_rate", "retention_rate"]
DRIVERS = [
    "marketing_spend", "discount_pct", "shipping_fee",
    "avg_selling_price", "inventory_available", "traffic",
]
TABLE_NAME = "product_performance"
COLUMNS = [
    "date", "product_id", "category",
    *DRIVERS, *METRICS,
]
QUERYABLE_TABLES = sorted(ALLOWED_TABLES)


def get_data_summary() -> dict[str, Any]:
    """Return a summary of what data is available for the planner."""
    try:
        from src.api.dependencies import get_historical_df_from_db
        df = get_historical_df_from_db()
    except Exception:
        csv_path = "temporal_dataset.csv"
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path, nrows=5000)
            df["date"] = pd.to_datetime(df["date"])
        else:
            return _empty_summary()

    if df.empty:
        return _empty_summary()

    return {
        "table": TABLE_NAME,
        "columns": COLUMNS,
        "metrics": METRICS,
        "drivers": DRIVERS,
        "queryable_tables": QUERYABLE_TABLES,
        "product_ids": sorted(df["product_id"].unique().tolist()),
        "categories": sorted(df["category"].unique().tolist()),
        "date_range": {
            "min": str(df["date"].min().date()),
            "max": str(df["date"].max().date()),
        },
        "total_rows": len(df),
    }


def get_data_summary_for_prompt() -> str:
    """Format the data summary as a text block for LLM prompt injection."""
    summary = get_data_summary()
    table_summaries = "\n".join(
        f"  - {name}: {TABLE_SCHEMAS[name]['description']}"
        for name in QUERYABLE_TABLES
        if name in TABLE_SCHEMAS
    )
    return (
        f"Primary table: {summary['table']}\n"
        f"Queryable tables (use nl2sql_query for ad-hoc factual questions):\n{table_summaries}\n"
        f"Available product IDs: {summary['product_ids']}\n"
        f"Available categories: {summary['categories']}\n"
        f"Date range: {summary['date_range']['min']} to {summary['date_range']['max']}\n"
        f"Predictable metrics: {summary['metrics']}\n"
        f"Controllable drivers: {summary['drivers']}"
    )


def _empty_summary() -> dict[str, Any]:
    """Fallback when no data source is available."""
    return {
        "table": TABLE_NAME,
        "columns": COLUMNS,
        "metrics": METRICS,
        "drivers": DRIVERS,
        "queryable_tables": QUERYABLE_TABLES,
        "product_ids": [],
        "categories": [],
        "date_range": {"min": "N/A", "max": "N/A"},
        "total_rows": 0,
    }
