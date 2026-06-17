import pandas as pd
from typing import Optional


def _safe_date(value) -> Optional[pd.Timestamp]:
    """Parse absolute or relative dates without raising. Returns None if invalid."""
    try:
        from src.core.nl2sql.dates import safe_parse_date
        return safe_parse_date(value)
    except Exception:
        try:
            return pd.to_datetime(value)
        except Exception:
            return None


def filter_dataframe(
    df: pd.DataFrame,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    product_id: Optional[str] = None,
    category: Optional[str] = None
) -> pd.DataFrame:
    """
    Standardized dataframe filtering helper to eliminate boilerplate date, product, 
    and category filtering across analytics modules.
    """
    df_filtered = df.copy()
    df_filtered["date"] = pd.to_datetime(df_filtered["date"])

    if start_date:
        parsed_start = _safe_date(start_date)
        if parsed_start is not None:
            df_filtered = df_filtered[df_filtered["date"] >= parsed_start]
    if end_date:
        parsed_end = _safe_date(end_date)
        if parsed_end is not None:
            df_filtered = df_filtered[df_filtered["date"] <= parsed_end]
    if product_id:
        df_filtered = df_filtered[df_filtered["product_id"] == product_id]
    if category:
        df_filtered = df_filtered[df_filtered["category"] == category]
        
    return df_filtered
