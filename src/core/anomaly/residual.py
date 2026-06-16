import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

class ResidualAnomalyDetector:
    def __init__(self, step_residuals: Dict[str, List[float]]):
        """
        step_residuals maps metric (lowercase) -> list of empirical standard deviations per forecast step
        """
        self.step_residuals = {k.lower(): v for k, v in step_residuals.items()}

    def detect_residuals(
        self,
        df_actual: pd.DataFrame,
        df_forecast: pd.DataFrame,
        product_id: str,
        target_metrics: Optional[List[str]] = None,
        window_type: str = "daily"
    ) -> List[Dict[str, Any]]:
        """
        Computes prediction vs. actual residuals, errors, and checks 95% confidence intervals.
        Supports daily, weekly, monthly, and custom window aggregations.
        """
        metrics = [m.lower() for m in (target_metrics or ["revenue", "profit", "orders", "conversion_rate", "retention_rate"])]
        
        # Filter datasets for product
        act_prod = df_actual[df_actual["product_id"] == product_id].copy()
        for_prod = df_forecast[df_forecast["product_id"] == product_id].copy()
        
        if len(act_prod) == 0 or len(for_prod) == 0:
            return []
            
        act_prod["date"] = pd.to_datetime(act_prod["date"])
        for_prod["date"] = pd.to_datetime(for_prod["date"])
        
        act_prod = act_prod.sort_values(by="date")
        for_prod = for_prod.sort_values(by="date")
        
        # Align dates: keep only dates that exist in both
        merged = pd.merge(
            act_prod, for_prod, on="date", suffixes=("_act", "_pred")
        ).sort_values(by="date").reset_index(drop=True)
        
        if len(merged) == 0:
            return []
            
        # Group dates based on window_type
        if window_type == "weekly":
            groups = merged.groupby(merged["date"].dt.to_period("W"))
        elif window_type == "monthly":
            groups = merged.groupby(merged["date"].dt.to_period("M"))
        else: # "daily" or "custom" (treated as daily points in details, aggregations handled on top)
            groups = merged.groupby(merged["date"])
            
        anomalies = []
        
        # We need historical errors to calculate Z-scores and standardize
        for period, group in groups:
            # Aggregate group values
            start_date = group["date"].min().strftime("%Y-%m-%d")
            end_date = group["date"].max().strftime("%Y-%m-%d")
            
            period_anomalies = {
                "period": str(period),
                "start_date": start_date,
                "end_date": end_date,
                "metrics": {}
            }
            
            for m in metrics:
                act_col = f"{m}_act"
                pred_col = f"{m}_pred"
                
                if act_col not in group.columns or pred_col not in group.columns:
                    continue
                    
                # Aggregate actual and predicted based on KPI type
                is_rate = m in ["conversion_rate", "retention_rate"]
                if is_rate:
                    act_val = float(group[act_col].mean())
                    pred_val = float(group[pred_col].mean())
                else:
                    act_val = float(group[act_col].sum())
                    pred_val = float(group[pred_col].sum())
                    
                residual = act_val - pred_val
                abs_err = abs(residual)
                pct_err = (residual / (act_val + 1e-5)) * 100.0 if act_val != 0 else 0.0
                rel_err = residual / (pred_val + 1e-5)
                
                # Fetch step-residuals standard errors to compute standardized metrics and 95% Confidence Intervals.
                # Find indices in forecast range
                std_errors = self.step_residuals.get(m, [0.0] * 100)
                
                # If grouped, sum or average std errors
                indices = group.index.tolist()
                group_std_errs = []
                for idx in indices:
                    # estimate forecast step index
                    step_idx = int(idx)
                    std_err = std_errors[step_idx] if step_idx < len(std_errors) else std_errors[-1]
                    group_std_errs.append(std_err)
                    
                # For sums, variance adds: std = sqrt(sum(var))
                # For rates, standard error of the mean: std = sqrt(sum(var)) / N
                if len(group_std_errs) > 0:
                    var_sum = sum(se**2 for se in group_std_errs)
                    if is_rate:
                        step_std = np.sqrt(var_sum) / len(group_std_errs)
                    else:
                        step_std = np.sqrt(var_sum)
                else:
                    step_std = 1.0
                    
                if step_std <= 0:
                    step_std = 1e-5
                    
                standardized_residual = residual / step_std
                
                # Confidence Interval (95%)
                margin = 1.96 * step_std
                conf_lower = max(0.0, pred_val - margin) if m in ["revenue", "orders"] else pred_val - margin
                if is_rate:
                    conf_lower = max(0.0, min(1.0, conf_lower))
                    conf_upper = max(0.0, min(1.0, pred_val + margin))
                else:
                    conf_upper = pred_val + margin
                    
                is_outside_ci = (act_val < conf_lower) or (act_val > conf_upper)
                
                # Residual Z-score (using standardized residual bounds)
                # Since standardized residual = residual / std, it acts as a z-score relative to forecast error distribution
                z_score = standardized_residual
                
                # Determine anomaly score impact (0-100)
                anomaly_score = min(100.0, max(0.0, abs(z_score) * 25.0)) # z_score >= 4 -> 100
                
                period_anomalies["metrics"][m] = {
                    "actual": round(act_val, 4),
                    "prediction": round(pred_val, 4),
                    "residual": round(residual, 4),
                    "absolute_error": round(abs_err, 4),
                    "percentage_error": round(pct_err, 2),
                    "relative_error": round(rel_err, 4),
                    "standardized_residual": round(standardized_residual, 4),
                    "z_score": round(z_score, 4),
                    "confidence_interval_95": [round(conf_lower, 4), round(conf_upper, 4)],
                    "outside_ci": is_outside_ci,
                    "anomaly_score": round(anomaly_score, 2)
                }
                
            anomalies.append(period_anomalies)
            
        return anomalies
