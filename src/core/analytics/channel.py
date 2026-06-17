import pandas as pd
from typing import Dict, Any, Optional

def analyze_channels(
    df: pd.DataFrame,
    product_id: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyzes sales mix and estimates absolute revenue & order distribution across sales channels.
    """
    from src.core.analytics.utils import filter_dataframe
    df_filtered = filter_dataframe(
        df, start_date=start_date, end_date=end_date, product_id=product_id, category=category
    )
        
    channels = {
        "Amazon": "amazon_sales_pct",
        "Website": "website_sales_pct",
        "Nykaa": "nykaa_sales_pct",
        "MobileApp": "mobile_app_sales_pct"
    }
    
    if len(df_filtered) == 0:
        return {
            "channel_mix": {c: 0.0 for c in channels},
            "estimated_revenue": {c: 0.0 for c in channels},
            "estimated_orders": {c: 0.0 for c in channels},
            "top_channel": {"channel": "None", "share": 0.0}
        }
        
    mix = {}
    est_rev = {}
    est_ord = {}
    
    total_rev = df_filtered["revenue"].sum()
    total_ord = df_filtered["orders"].sum()
    
    for c_name, c_col in channels.items():
        if c_col in df_filtered.columns:
            # Average share in mix
            avg_share = float(df_filtered[c_col].mean())
            mix[c_name] = round(avg_share, 2)
            
            # Weighted estimated revenue: sum of (row_rev * row_share / 100)
            weighted_rev = float((df_filtered["revenue"] * df_filtered[c_col] / 100.0).sum())
            est_rev[c_name] = round(weighted_rev, 2)
            
            # Weighted estimated orders: sum of (row_orders * row_share / 100)
            weighted_ord = float((df_filtered["orders"] * df_filtered[c_col] / 100.0).sum())
            est_ord[c_name] = round(weighted_ord, 2)
        else:
            mix[c_name] = 0.0
            est_rev[c_name] = 0.0
            est_ord[c_name] = 0.0
            
    # Determine top channel by average mix share
    top_c = max(mix, key=mix.get)
    top_share = mix[top_c]
    
    return {
        "channel_mix": mix,
        "estimated_revenue": est_rev,
        "estimated_orders": est_ord,
        "top_channel": {"channel": top_c, "share": top_share}
    }
