import pandas as pd
import numpy as np
from scipy.stats import linregress
from typing import Dict, Any, Optional

def analyze_trends(
    df: pd.DataFrame,
    metric: str = "revenue",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    product_id: Optional[str] = None,
    granularity: str = "daily"
) -> Dict[str, Any]:
    """
    Analyzes trajectories and performs regression over time for a target metric with custom granularity.
    """
    from src.core.analytics.utils import filter_dataframe
    df_filtered = filter_dataframe(
        df, start_date=start_date, end_date=end_date, product_id=product_id
    )
        
    metric_lower = metric.lower()
    if metric_lower not in df_filtered.columns:
        metric_lower = "revenue"
        
    # Apply time granularity grouping
    gran_lower = granularity.lower() if granularity else "daily"
    if gran_lower == "weekly":
        df_filtered["date"] = df_filtered["date"].dt.to_period('W').dt.start_time
    elif gran_lower == "monthly":
        df_filtered["date"] = df_filtered["date"].dt.to_period('M').dt.start_time
    elif gran_lower == "quarterly":
        df_filtered["date"] = df_filtered["date"].dt.to_period('Q').dt.start_time
        
    # Determine aggregation function
    mean_metrics = [
        "conversion_rate", "retention_rate", "avg_selling_price", 
        "discount_pct", "shipping_fee", "current_ctr", "current_roas", 
        "avg_ltv", "price_index"
    ]
    agg_func = "mean" if metric_lower in mean_metrics else "sum"
    
    df_grouped = df_filtered.groupby("date")[metric_lower].agg(agg_func).reset_index()
    df_grouped = df_grouped.sort_values(by="date")
    
    if len(df_grouped) < 2:
        return {
            "metric": metric_lower,
            "direction": "stable",
            "slope": 0.0,
            "r_squared": 0.0,
            "p_value": 1.0,
            "growth_rate_pct": 0.0,
            "history": []
        }
        
    day_indices = (df_grouped["date"] - df_grouped["date"].min()).dt.days.values
    values = df_grouped[metric_lower].values
    
    slope, intercept, r_value, p_value, std_err = linregress(day_indices, values)
    
    start_val = np.mean(values[:max(1, len(values)//10)]) if len(values) >= 10 else values[0]
    end_val = np.mean(values[-max(1, len(values)//10):]) if len(values) >= 10 else values[-1]
    
    growth_rate = ((end_val - start_val) / start_val * 100.0) if start_val > 0 else 0.0
    
    # Classify direction
    if p_value < 0.05:
        direction = "increasing" if slope > 0 else "decreasing"
    else:
        direction = "stable"
        
    history = [
        {"date": row["date"].strftime("%Y-%m-%d"), "value": round(float(row[metric_lower]), 2)}
        for _, row in df_grouped.iterrows()
    ]
    
    return {
        "metric": metric_lower,
        "granularity": gran_lower,
        "direction": direction,
        "slope": round(float(slope), 4),
        "r_squared": round(float(r_value ** 2), 4),
        "p_value": round(float(p_value), 6),
        "growth_rate_pct": round(float(growth_rate), 2),
        "history": history[:100]  # Cap history size for JSON response
    }
