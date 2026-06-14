import pandas as pd
from typing import Dict, Any, Optional

def analyze_benchmarks(
    df: pd.DataFrame,
    product_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compares a product's performance to category and global benchmarks.
    """
    df_filtered = df.copy()
    df_filtered["date"] = pd.to_datetime(df_filtered["date"])
    
    if start_date:
        df_filtered = df_filtered[df_filtered["date"] >= pd.to_datetime(start_date)]
    if end_date:
        df_filtered = df_filtered[df_filtered["date"] <= pd.to_datetime(end_date)]
        
    prod_data = df_filtered[df_filtered["product_id"] == product_id]
    if len(prod_data) == 0:
        return {
            "product_id": product_id,
            "category": "Unknown",
            "comparisons": {}
        }
        
    category = prod_data["category"].iloc[0]
    cat_data = df_filtered[df_filtered["category"] == category]
    
    # Helper to calculate metrics for a subset of data
    def compute_metrics(subset: pd.DataFrame) -> Dict[str, float]:
        if len(subset) == 0:
            return {"asp": 0.0, "cvr": 0.0, "retention": 0.0, "profit_margin": 0.0, "marketing_efficiency": 0.0}
        
        rev = subset["revenue"].sum()
        prof = subset["profit"].sum()
        spend = subset["marketing_spend"].sum()
        
        return {
            "asp": float(subset["avg_selling_price"].mean()),
            "cvr": float(subset["conversion_rate"].mean()),
            "retention": float(subset["retention_rate"].mean()),
            "profit_margin": float(prof / rev) if rev > 0 else 0.0,
            "marketing_efficiency": float(rev / spend) if spend > 0 else 0.0
        }
        
    prod_metrics = compute_metrics(prod_data)
    cat_metrics = compute_metrics(cat_data)
    global_metrics = compute_metrics(df_filtered)
    
    comparisons = {}
    for key in ["asp", "cvr", "retention", "profit_margin", "marketing_efficiency"]:
        p_val = prod_metrics[key]
        c_val = cat_metrics[key]
        g_val = global_metrics[key]
        
        comparisons[key] = {
            "product_value": round(p_val, 4),
            "category_benchmark": round(c_val, 4),
            "global_benchmark": round(g_val, 4),
            "pct_vs_category": round((p_val - c_val) / c_val * 100.0, 2) if c_val > 0 else 0.0,
            "pct_vs_global": round((p_val - g_val) / g_val * 100.0, 2) if g_val > 0 else 0.0
        }
        
    return {
        "product_id": product_id,
        "category": category,
        "comparisons": comparisons
    }
