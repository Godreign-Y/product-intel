import pandas as pd
from typing import Dict, Any, Optional

def analyze_seasonality(
    df: pd.DataFrame,
    product_id: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyzes seasonal effects: day-of-week, weekend vs weekday, and monthly averages.
    """
    from src.core.analytics.utils import filter_dataframe
    df_filtered = filter_dataframe(
        df, start_date=start_date, end_date=end_date, product_id=product_id, category=category
    )
        
    if len(df_filtered) == 0:
        return {
            "day_of_week_avg": {},
            "weekend_vs_weekday": {},
            "monthly_avg": {}
        }
        
    df_filtered["day_name"] = df_filtered["date"].dt.day_name()
    df_filtered["month_name"] = df_filtered["date"].dt.strftime("%B")
    df_filtered["is_weekend"] = df_filtered["date"].dt.dayofweek >= 5
    
    # Day of week average
    dow_grouped = df_filtered.groupby("day_name")[["revenue", "orders"]].mean().reset_index()
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    dow_grouped["day_name"] = pd.Categorical(dow_grouped["day_name"], categories=day_order, ordered=True)
    dow_grouped = dow_grouped.sort_values("day_name")
    
    day_of_week_avg = {
        row["day_name"]: {
            "revenue": round(float(row["revenue"]), 2),
            "orders": round(float(row["orders"]), 2)
        }
        for _, row in dow_grouped.iterrows()
    }
    
    # Weekend vs Weekday
    w_grouped = df_filtered.groupby("is_weekend")[["revenue", "orders"]].mean().reset_index()
    weekday_row = w_grouped[w_grouped["is_weekend"] == False]
    weekend_row = w_grouped[w_grouped["is_weekend"] == True]
    
    weekday_rev = float(weekday_row["revenue"].iloc[0]) if len(weekday_row) > 0 else 0.0
    weekend_rev = float(weekend_row["revenue"].iloc[0]) if len(weekend_row) > 0 else 0.0
    weekday_ord = float(weekday_row["orders"].iloc[0]) if len(weekday_row) > 0 else 0.0
    weekend_ord = float(weekend_row["orders"].iloc[0]) if len(weekend_row) > 0 else 0.0
    
    weekend_vs_weekday = {
        "weekday": {
            "revenue": round(weekday_rev, 2),
            "orders": round(weekday_ord, 2)
        },
        "weekend": {
            "revenue": round(weekend_rev, 2),
            "orders": round(weekend_ord, 2)
        },
        "revenue_lift_pct": round((weekend_rev - weekday_rev) / weekday_rev * 100.0, 2) if weekday_rev > 0 else 0.0,
        "orders_lift_pct": round((weekend_ord - weekday_ord) / weekday_ord * 100.0, 2) if weekday_ord > 0 else 0.0
    }
    
    # Monthly averages
    month_order = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    m_grouped = df_filtered.groupby("month_name")[["revenue", "orders"]].mean().reset_index()
    m_grouped["month_name"] = pd.Categorical(m_grouped["month_name"], categories=month_order, ordered=True)
    m_grouped = m_grouped.sort_values("month_name").dropna()
    
    monthly_avg = {
        row["month_name"]: {
            "revenue": round(float(row["revenue"]), 2),
            "orders": round(float(row["orders"]), 2)
        }
        for _, row in m_grouped.iterrows()
    }
    
    return {
        "day_of_week_avg": day_of_week_avg,
        "weekend_vs_weekday": weekend_vs_weekday,
        "monthly_avg": monthly_avg
    }
