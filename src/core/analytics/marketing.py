import pandas as pd
from typing import Dict, Any, Optional

def analyze_marketing(
    df: pd.DataFrame,
    product_id: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluates marketing efficiency: spend, CTR, ROAS, and correlation with revenue.
    """
    from src.core.analytics.utils import filter_dataframe
    df_filtered = filter_dataframe(
        df, start_date=start_date, end_date=end_date, product_id=product_id, category=category
    )
        
    if len(df_filtered) == 0:
        return {
            "total_marketing_spend": 0.0,
            "average_roas": 0.0,
            "average_ctr": 0.0,
            "marketing_spend_to_revenue_ratio": 0.0,
            "spend_revenue_correlation": 0.0
        }
        
    total_spend = float(df_filtered["marketing_spend"].sum())
    total_revenue = float(df_filtered["revenue"].sum())
    avg_roas = float(df_filtered["current_roas"].mean())
    avg_ctr = float(df_filtered["current_ctr"].mean())
    
    # Calculate spend to revenue ratio
    ratio = total_spend / total_revenue if total_revenue > 0 else 0.0
    
    # Calculate Pearson Correlation between marketing_spend and revenue
    if len(df_filtered) >= 2 and df_filtered["marketing_spend"].std() > 0 and df_filtered["revenue"].std() > 0:
        correlation = float(df_filtered["marketing_spend"].corr(df_filtered["revenue"]))
        if pd.isna(correlation):
            correlation = 0.0
    else:
        correlation = 0.0
        
    return {
        "total_marketing_spend": round(total_spend, 2),
        "average_roas": round(avg_roas, 4),
        "average_ctr": round(avg_ctr, 4),
        "marketing_spend_to_revenue_ratio": round(ratio, 4),
        "spend_revenue_correlation": round(correlation, 4)
    }
