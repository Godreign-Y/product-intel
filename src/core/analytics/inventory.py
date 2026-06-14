import pandas as pd
from typing import Dict, Any, Optional

def analyze_inventory(
    df: pd.DataFrame,
    product_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Assesses stock health, turnover rate, and stockout risk for a specific product.
    """
    df_filtered = df.copy()
    df_filtered["date"] = pd.to_datetime(df_filtered["date"])
    
    if start_date:
        df_filtered = df_filtered[df_filtered["date"] >= pd.to_datetime(start_date)]
    if end_date:
        df_filtered = df_filtered[df_filtered["date"] <= pd.to_datetime(end_date)]
        
    prod_data = df_filtered[df_filtered["product_id"] == product_id].sort_values(by="date")
    if len(prod_data) == 0:
        return {
            "product_id": product_id,
            "current_stock": 0,
            "average_stock": 0.0,
            "estimated_days_of_stock": 0.0,
            "stockout_risk": "Low",
            "inventory_ratio_avg": 0.0
        }
        
    current_stock = int(prod_data["inventory_available"].iloc[-1])
    avg_stock = float(prod_data["inventory_available"].mean())
    
    # Calculate daily order velocity
    days = len(prod_data["date"].unique())
    total_orders = prod_data["orders"].sum()
    daily_sales_avg = total_orders / days if days > 0 else 0.0
    
    if daily_sales_avg > 0:
        days_of_stock = current_stock / daily_sales_avg
    else:
        days_of_stock = 999.0  # Safe boundary if no sales are occurring
        
    if days_of_stock < 7:
        risk = "High"
    elif days_of_stock < 21:
        risk = "Medium"
    else:
        risk = "Low"
        
    inv_ratio = float((prod_data["inventory_available"] / (prod_data["traffic"] + 1e-5)).mean())
    
    return {
        "product_id": product_id,
        "current_stock": current_stock,
        "average_stock": round(avg_stock, 2),
        "estimated_days_of_stock": round(days_of_stock, 2),
        "stockout_risk": risk,
        "inventory_ratio_avg": round(inv_ratio, 4)
    }
