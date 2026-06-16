import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
import datetime
from scipy import stats
from src.core.history.storage.models import Experiment

class ExperimentDetector:
    def __init__(self, window_days: int = 14, min_duration: int = 7):
        self.window_days = window_days
        self.min_duration = min_duration

    def infer_experiments(self, df_hist: pd.DataFrame) -> List[Experiment]:
        """
        Scans driver metrics in time-series data to detect step-changes and group them as experiments.
        """
        experiments = []
        df = df_hist.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values(by=["product_id", "date"]).reset_index(drop=True)
        
        # Drivers to monitor and their thresholds (relative or absolute)
        drivers = {
            "avg_selling_price": {"type": "rel", "threshold": 0.05, "name": "Pricing Experiment"},
            "discount_pct": {"type": "abs", "threshold": 5.0, "name": "Discount Experiment"},
            "marketing_spend": {"type": "rel", "threshold": 0.30, "name": "Marketing Spend Experiment"},
            "shipping_fee": {"type": "abs", "threshold": 5.0, "name": "Shipping Fee Experiment"}
        }
        
        # Scan product groups
        for product_id, group in df.groupby("product_id"):
            group = group.sort_values(by="date").reset_index(drop=True)
            if len(group) < (self.window_days * 2) + self.min_duration:
                continue
                
            brand = group["brand"].iloc[0] if "brand" in group.columns else "Generic"
            category = group["category"].iloc[0] if "category" in group.columns else "Generic"
            
            for col, config in drivers.items():
                col_type = config["type"]
                thresh = config["threshold"]
                exp_name = config["name"]
                
                i = self.window_days
                while i < len(group) - self.window_days:
                    row = group.iloc[i]
                    date_val = row["date"].date()
                    
                    # Compute window before and after averages
                    before_slice = group.iloc[i - self.window_days : i]
                    after_slice = group.iloc[i : i + self.window_days]
                    
                    before_mean = before_slice[col].mean()
                    after_mean = after_slice[col].mean()
                    
                    is_step_change = False
                    if before_mean > 0:
                        if col_type == "rel":
                            diff_pct = abs(after_mean - before_mean) / before_mean
                            is_step_change = diff_pct >= thresh
                        else:
                            is_step_change = abs(after_mean - before_mean) >= thresh
                            
                    if is_step_change:
                        # Find end of the experiment (when the variable changes again or lookahead window ends)
                        start_date = date_val
                        end_date = group.iloc[min(len(group)-1, i + self.window_days - 1)]["date"].date()
                        
                        # Calculate pre- and post-KPIs
                        kpis = ["revenue", "profit", "orders", "conversion_rate", "retention_rate"]
                        before_metrics = {}
                        after_metrics = {}
                        
                        for kpi in kpis:
                            before_metrics[kpi] = round(float(before_slice[kpi].mean()), 4)
                            after_metrics[kpi] = round(float(after_slice[kpi].mean()), 4)
                            
                        # Statistical significance check (Welch's t-test) on primary target KPI
                        # Primary targets:
                        # - price -> conversion_rate or revenue
                        # - discount -> conversion_rate or profit
                        # - marketing -> revenue or orders
                        # - shipping -> conversion_rate
                        primary_kpi = "conversion_rate"
                        if col == "avg_selling_price" or col == "marketing_spend":
                            primary_kpi = "revenue"
                        elif col == "discount_pct":
                            primary_kpi = "profit"
                            
                        t_stat, p_val = stats.ttest_ind(
                            before_slice[primary_kpi].values,
                            after_slice[primary_kpi].values,
                            equal_var=False
                        )
                        
                        # Determine Outcome
                        before_target = before_metrics[primary_kpi]
                        after_target = after_metrics[primary_kpi]
                        target_diff = after_target - before_target
                        
                        if pd.isna(p_val):
                            p_val = 0.5
                            
                        # Confidence score based on p-value
                        confidence = 1.0 - p_val
                        confidence = min(0.99, max(0.50, confidence))
                        
                        if p_val < 0.10:
                            if target_diff > 0:
                                outcome = "positive"
                            else:
                                outcome = "negative"
                        else:
                            outcome = "neutral"
                            
                        # Compute overall improvement %
                        improvement = 0.0
                        if before_target > 0:
                            improvement = (target_diff / before_target) * 100.0
                            
                        # Construct a unique experiment ID
                        exp_id = f"EXP_{col[:3].upper()}_{product_id}_{start_date.strftime('%m%d')}"
                        
                        change_direction = "increased" if after_mean > before_mean else "decreased"
                        change_summary = (
                            f"Driver '{col}' was {change_direction} from an average of "
                            f"{before_mean:.2f} to {after_mean:.2f} starting on {start_date.strftime('%Y-%m-%d')}."
                        )
                        
                        exp_instance = Experiment(
                            experiment_id=exp_id,
                            type=exp_name,
                            product_ids=product_id,
                            category=category,
                            brand=brand,
                            start_date=start_date,
                            end_date=end_date,
                            before_metrics=before_metrics,
                            after_metrics=after_metrics,
                            change_summary=change_summary,
                            improvement_pct=round(float(improvement), 2),
                            outcome=outcome,
                            confidence_score=round(float(confidence), 2)
                        )
                        experiments.append(exp_instance)
                        
                        # Advance iterator past lookahead window to prevent overlapping detection of the same shift
                        i += self.window_days
                        continue
                        
                    i += 1
                    
        # Filter duplicates (keep chronological list)
        seen_ids = set()
        unique_experiments = []
        for exp in experiments:
            if exp.experiment_id not in seen_ids:
                seen_ids.add(exp.experiment_id)
                unique_experiments.append(exp)
                
        return unique_experiments
