import pandas as pd
from typing import Dict, Any, Optional

def analyze_kpis(
    df: pd.DataFrame,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    product_id: Optional[str] = None,
    category: Optional[str] = None
) -> Dict[str, Any]:
    """
    Computes aggregates and averages for primary KPIs.
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
        
    days = len(df_filtered["date"].unique())
    if len(df_filtered) == 0 or days == 0:
        return {
            "revenue": {"sum": 0.0, "daily_avg": 0.0},
            "profit": {"sum": 0.0, "daily_avg": 0.0, "profit_margin": 0.0},
            "orders": {"sum": 0.0, "daily_avg": 0.0},
            "traffic": {"sum": 0.0, "daily_avg": 0.0},
            "conversion_rate": {"mean": 0.0},
            "retention_rate": {"mean": 0.0},
            "marketing_spend": {"sum": 0.0, "daily_avg": 0.0},
            "days_in_period": 0
        }
        
    revenue_sum = float(df_filtered["revenue"].sum())
    profit_sum = float(df_filtered["profit"].sum())
    orders_sum = float(df_filtered["orders"].sum())
    traffic_sum = float(df_filtered["traffic"].sum())
    marketing_sum = float(df_filtered["marketing_spend"].sum())
    
    average_order_value = float(revenue_sum / orders_sum) if orders_sum > 0 else 0.0
    
    return {
        "revenue": {
            "sum": round(revenue_sum, 2),
            "daily_avg": round(revenue_sum / days, 2)
        },
        "profit": {
            "sum": round(profit_sum, 2),
            "daily_avg": round(profit_sum / days, 2),
            "profit_margin": round(profit_sum / revenue_sum, 4) if revenue_sum > 0 else 0.0
        },
        "orders": {
            "sum": round(orders_sum, 2),
            "daily_avg": round(orders_sum / days, 2)
        },
        "traffic": {
            "sum": round(traffic_sum, 2),
            "daily_avg": round(traffic_sum / days, 2)
        },
        "conversion_rate": {
            "mean": round(float(df_filtered["conversion_rate"].mean()), 4)
        },
        "retention_rate": {
            "mean": round(float(df_filtered["retention_rate"].mean()), 4)
        },
        "marketing_spend": {
            "sum": round(marketing_sum, 2),
            "daily_avg": round(marketing_sum / days, 2)
        },
        "average_order_value": round(average_order_value, 2),
        "days_in_period": days
    }
