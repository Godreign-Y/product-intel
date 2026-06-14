import pandas as pd
from typing import Dict, Any, Optional

def analyze_customers(
    df: pd.DataFrame,
    product_id: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Computes Customer metrics including average LTV, user activity, retention, and age-group breakdown.
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
        
    if len(df_filtered) == 0:
        return {
            "average_ltv": 0.0,
            "active_users": {"mean": 0.0, "max": 0.0},
            "retention_rate_avg": 0.0,
            "age_group_distribution": {}
        }
        
    avg_ltv = float(df_filtered["avg_ltv"].mean()) if "avg_ltv" in df_filtered.columns else 0.0
    mean_active = float(df_filtered["active_users"].mean()) if "active_users" in df_filtered.columns else 0.0
    max_active = float(df_filtered["active_users"].max()) if "active_users" in df_filtered.columns else 0.0
    avg_ret = float(df_filtered["retention_rate"].mean())
    
    # Age group distribution
    age_dist = {}
    if "dominant_age_group" in df_filtered.columns:
        counts = df_filtered["dominant_age_group"].value_counts(normalize=True)
        age_dist = {str(k): round(float(v) * 100.0, 2) for k, v in counts.items()}
        
    return {
        "average_ltv": round(avg_ltv, 2),
        "active_users": {
            "mean": round(mean_active, 2),
            "max": int(max_active)
        },
        "retention_rate_avg": round(avg_ret, 4),
        "age_group_distribution": age_dist
    }
