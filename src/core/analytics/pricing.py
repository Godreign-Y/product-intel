import pandas as pd
from typing import Dict, Any, Optional

def analyze_pricing(
    df: pd.DataFrame,
    product_id: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyzes pricing metrics, discount buckets performance, and price elasticity estimates.
    """
    from src.core.analytics.utils import filter_dataframe
    df_filtered = filter_dataframe(
        df, start_date=start_date, end_date=end_date, product_id=product_id, category=category
    )
        
    if len(df_filtered) == 0:
        return {
            "average_price": 0.0,
            "average_discount": 0.0,
            "discount_buckets_performance": {},
            "price_elasticity_estimate": 0.0
        }
        
    avg_price = float(df_filtered["avg_selling_price"].mean())
    avg_disc = float(df_filtered["discount_pct"].mean())
    
    # Calculate discount buckets performance
    # Define bucket rules
    buckets = [
        ("0-10%", lambda x: x["discount_pct"] <= 10.0),
        ("10-20%", lambda x: (x["discount_pct"] > 10.0) & (x["discount_pct"] <= 20.0)),
        ("20-30%", lambda x: (x["discount_pct"] > 20.0) & (x["discount_pct"] <= 30.0)),
        ("30%+", lambda x: x["discount_pct"] > 30.0)
    ]
    
    bucket_perf = {}
    for name, condition in buckets:
        sub_df = df_filtered[condition(df_filtered)]
        if len(sub_df) > 0:
            bucket_perf[name] = {
                "average_price": round(float(sub_df["avg_selling_price"].mean()), 2),
                "average_orders": round(float(sub_df["orders"].mean()), 2),
                "average_revenue": round(float(sub_df["revenue"].mean()), 2),
                "average_conversion_rate": round(float(sub_df["conversion_rate"].mean()), 4),
                "sample_count": len(sub_df)
            }
        else:
            bucket_perf[name] = {
                "average_price": 0.0,
                "average_orders": 0.0,
                "average_revenue": 0.0,
                "average_conversion_rate": 0.0,
                "sample_count": 0
            }
            
    # Calculate price elasticity estimate: correlation between price and orders
    if len(df_filtered) >= 2 and df_filtered["avg_selling_price"].std() > 0 and df_filtered["orders"].std() > 0:
        elasticity_corr = float(df_filtered["avg_selling_price"].corr(df_filtered["orders"]))
        if pd.isna(elasticity_corr):
            elasticity_corr = 0.0
    else:
        elasticity_corr = 0.0
        
    return {
        "average_price": round(avg_price, 2),
        "average_discount": round(avg_disc, 2),
        "discount_buckets_performance": bucket_perf,
        "price_elasticity_estimate": round(elasticity_corr, 4)
    }
