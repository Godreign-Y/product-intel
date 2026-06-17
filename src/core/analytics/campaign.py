import pandas as pd
from typing import Dict, Any, Optional

def analyze_campaigns(
    df: pd.DataFrame,
    product_id: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyzes campaign spend allocation and general marketing effectiveness metrics.
    """
    from src.core.analytics.utils import filter_dataframe
    df_filtered = filter_dataframe(
        df, start_date=start_date, end_date=end_date, product_id=product_id, category=category
    )
        
    campaigns = {
        "Search": "search_campaign_pct",
        "Social": "social_campaign_pct",
        "Email": "email_campaign_pct",
        "Affiliate": "affiliate_campaign_pct"
    }
    
    if len(df_filtered) == 0:
        return {
            "campaign_mix": {c: 0.0 for c in campaigns},
            "estimated_spend": {c: 0.0 for c in campaigns},
            "top_campaign_type": {"campaign": "None", "share": 0.0},
            "general_metrics": {"avg_ctr": 0.0, "avg_roas": 0.0}
        }
        
    mix = {}
    est_spend = {}
    
    for c_name, c_col in campaigns.items():
        if c_col in df_filtered.columns:
            avg_share = float(df_filtered[c_col].mean())
            mix[c_name] = round(avg_share, 2)
            
            # Weighted estimated spend: sum of (row_spend * row_share / 100)
            weighted_spend = float((df_filtered["marketing_spend"] * df_filtered[c_col] / 100.0).sum())
            est_spend[c_name] = round(weighted_spend, 2)
        else:
            mix[c_name] = 0.0
            est_spend[c_name] = 0.0
            
    # Top campaign
    top_c = max(mix, key=mix.get)
    top_share = mix[top_c]
    
    avg_ctr = float(df_filtered["current_ctr"].mean()) if "current_ctr" in df_filtered.columns else 0.0
    avg_roas = float(df_filtered["current_roas"].mean()) if "current_roas" in df_filtered.columns else 0.0
    
    return {
        "campaign_mix": mix,
        "estimated_spend": est_spend,
        "top_campaign_type": {"campaign": top_c, "share": top_share},
        "general_metrics": {
            "avg_ctr": round(avg_ctr, 4),
            "avg_roas": round(avg_roas, 4)
        }
    }
