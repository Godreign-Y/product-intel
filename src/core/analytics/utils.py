import pandas as pd
from typing import Optional

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
        df_filtered = df_filtered[df_filtered["date"] >= pd.to_datetime(start_date)]
    if end_date:
        df_filtered = df_filtered[df_filtered["date"] <= pd.to_datetime(end_date)]
    if product_id:
        df_filtered = df_filtered[df_filtered["product_id"] == product_id]
    if category:
        df_filtered = df_filtered[df_filtered["category"] == category]
        
    return df_filtered
