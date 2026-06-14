import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from scipy.stats import linregress
from src.utils.logger import setup_logger

logger = setup_logger("analyzer")

class BusinessAnalyzer:
    def __init__(self):
        pass

    def compare_periods(
        self,
        df: pd.DataFrame,
        period1_start: str,
        period1_end: str,
        period2_start: str,
        period2_end: str,
        product_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compares business metrics and drivers between two custom date periods.
        """
        df_copy = df.copy()
        df_copy["date"] = pd.to_datetime(df_copy["date"])
        
        if product_id:
            df_copy = df_copy[df_copy["product_id"] == product_id]
            
        p1_start = pd.to_datetime(period1_start)
        p1_end = pd.to_datetime(period1_end)
        p2_start = pd.to_datetime(period2_start)
        p2_end = pd.to_datetime(period2_end)
        
        p1_df = df_copy[(df_copy["date"] >= p1_start) & (df_copy["date"] <= p1_end)]
        p2_df = df_copy[(df_copy["date"] >= p2_start) & (df_copy["date"] <= p2_end)]
        
        metrics = ["revenue", "profit", "orders", "traffic", "marketing_spend"]
        rates = ["conversion_rate", "retention_rate", "discount_pct", "shipping_fee"]
        
        comparison = {}
        
        for m in metrics:
            p1_val = float(p1_df[m].sum()) if len(p1_df) > 0 else 0.0
            p2_val = float(p2_df[m].sum()) if len(p2_df) > 0 else 0.0
            diff = p2_val - p1_val
            pct_diff = (diff / p1_val * 100.0) if p1_val != 0 else 0.0
            comparison[m] = {
                "period1_sum": round(p1_val, 2),
                "period2_sum": round(p2_val, 2),
                "difference": round(diff, 2),
                "percentage_change": round(pct_diff, 2)
            }
            
        for r in rates:
            p1_val = float(p1_df[r].mean()) if len(p1_df) > 0 else 0.0
            p2_val = float(p2_df[r].mean()) if len(p2_df) > 0 else 0.0
            diff = p2_val - p1_val
            pct_diff = (diff / p1_val * 100.0) if p1_val != 0 else 0.0
            comparison[r] = {
                "period1_mean": round(p1_val, 4),
                "period2_mean": round(p2_val, 4),
                "difference": round(diff, 4),
                "percentage_change": round(pct_diff, 2)
            }
            
        # Determine the key drivers of the changes (for LLM context)
        drivers_report = []
        
        rev_change = comparison["revenue"]["percentage_change"]
        if abs(rev_change) > 1.0:
            direction = "increased" if rev_change > 0 else "decreased"
            mkt_change = comparison["marketing_spend"]["percentage_change"]
            disc_change = comparison["discount_pct"]["difference"]
            views_change = comparison["traffic"]["percentage_change"]
            
            drivers_report.append(f"Revenue {direction} by {abs(rev_change):.1f}% from Period 1 to Period 2.")
            
            if mkt_change < -5.0 and direction == "decreased":
                drivers_report.append(f"A drop in marketing spend of {abs(mkt_change):.1f}% likely reduced visibility.")
            elif mkt_change > 5.0 and direction == "increased":
                drivers_report.append(f"Marketing spend increased by {abs(mkt_change):.1f}%, driving traffic.")
                
            if views_change < -5.0:
                drivers_report.append(f"Traffic fell by {abs(views_change):.1f}%, indicating lower interest.")
            elif views_change > 5.0:
                drivers_report.append(f"Traffic rose by {abs(views_change):.1f}%, expanding the sales funnel.")
                
            # Account for discount scale difference (0-100 vs 0-1)
            disc_scale = 1.0 if comparison["discount_pct"]["period1_mean"] <= 1.0 else 100.0
            disc_diff_pct = disc_change / disc_scale * 100.0
            
            if disc_diff_pct > 1.0 and direction == "increased":
                drivers_report.append(f"Average discount rate increased by {abs(disc_diff_pct):.1f} percentage points, boosting conversions.")
            elif disc_diff_pct < -1.0 and direction == "decreased":
                drivers_report.append(f"Average discount rate decreased by {abs(disc_diff_pct):.1f} percentage points, reducing order volume.")

        return {
            "period1_range": f"{period1_start} to {period1_end}",
            "period2_range": f"{period2_start} to {period2_end}",
            "product_id": product_id,
            "metrics_comparison": comparison,
            "drivers_summary": drivers_report
        }

    def detect_declining_products(
        self,
        df: pd.DataFrame,
        lookback_days: int = 90,
        metric: str = "revenue"
    ) -> List[Dict[str, Any]]:
        """
        Identifies which products are on a declining trend over the last lookback_days.
        """
        df_copy = df.copy()
        df_copy["date"] = pd.to_datetime(df_copy["date"])
        
        metric_lower = metric.lower()
        if metric_lower not in df_copy.columns:
            # Fallback
            metric_lower = "revenue"
            
        max_date = df_copy["date"].max()
        cutoff_date = max_date - pd.Timedelta(days=lookback_days)
        
        recent_df = df_copy[df_copy["date"] >= cutoff_date]
        
        declining_list = []
        
        for prod_id, group in recent_df.groupby("product_id"):
            group = group.sort_values(by="date")
            if len(group) < 10:
                continue
                
            day_indices = (group["date"] - group["date"].min()).dt.days.values
            values = group[metric_lower].values
            
            slope, intercept, r_value, p_value, std_err = linregress(day_indices, values)
            
            start_val = np.mean(values[:5]) if len(values) >= 5 else values[0]
            end_val = np.mean(values[-5:]) if len(values) >= 5 else values[-1]
            total_change = end_val - start_val
            pct_change = (total_change / start_val * 100.0) if start_val != 0 else 0.0
            
            if slope < 0 and pct_change < -5.0:
                declining_list.append({
                    "product_id": prod_id,
                    "category": group["category"].iloc[0],
                    "slope": float(slope),
                    "total_change": round(float(total_change), 2),
                    "percentage_change": round(float(pct_change), 2),
                    "r_squared": float(r_value ** 2),
                    "p_value": float(p_value)
                })
                
        declining_list = sorted(declining_list, key=lambda x: x["percentage_change"])
        return declining_list
