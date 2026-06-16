import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

class HistoricalAnomalyContext:
    def __init__(self):
        pass

    def evaluate_historical_context(
        self,
        df_actual: pd.DataFrame,
        df_forecast: pd.DataFrame,
        product_id: str,
        kpi: str,
        current_date: str,
        current_severity: float,
        current_change_pct: float
    ) -> Dict[str, Any]:
        """
        Scans product history for past anomalies in the same KPI to compute frequency, severity, and similarity.
        """
        kpi_lower = kpi.lower()
        act_prod = df_actual[df_actual["product_id"] == product_id].copy()
        for_prod = df_forecast[df_forecast["product_id"] == product_id].copy()
        
        if len(act_prod) == 0 or len(for_prod) == 0:
            return {"has_occurred_before": False}
            
        act_prod["date"] = pd.to_datetime(act_prod["date"])
        for_prod["date"] = pd.to_datetime(for_prod["date"])
        
        merged = pd.merge(
            act_prod, for_prod, on="date", suffixes=("_act", "_pred")
        ).sort_values(by="date")
        
        current_ts = pd.to_datetime(current_date)
        historical_merged = merged[merged["date"] < current_ts].copy()
        
        if len(historical_merged) == 0:
            return {"has_occurred_before": False}
            
        # 1. Detect past anomalies using a simple threshold (deviation > 10% or Z-score > 2.0)
        # To find historical standard errors, compute std of history
        act_vals = historical_merged[f"{kpi_lower}_act"].values
        pred_vals = historical_merged[f"{kpi_lower}_pred"].values
        
        residuals = act_vals - pred_vals
        res_std = np.std(residuals) if np.std(residuals) > 0 else 1.0
        
        past_anomalies = []
        consecutive_days = 0
        recovery_times = []
        
        for idx, row in historical_merged.iterrows():
            date_str = row["date"].strftime("%Y-%m-%d")
            act_val = row[f"{kpi_lower}_act"]
            pred_val = row[f"{kpi_lower}_pred"]
            res = act_val - pred_val
            pct_chg = (res / (pred_val + 1e-5)) * 100.0
            
            # Simple threshold check
            z = res / res_std
            if abs(z) > 2.0:
                consecutive_days += 1
                past_anomalies.append({
                    "date": date_str,
                    "actual": act_val,
                    "prediction": pred_val,
                    "residual": res,
                    "percentage_change": pct_chg,
                    "z_score": z,
                    "severity": min(100.0, abs(z) * 25.0)
                })
            else:
                if consecutive_days > 0:
                    recovery_times.append(consecutive_days)
                    consecutive_days = 0
                    
        if consecutive_days > 0:
            recovery_times.append(consecutive_days)
            
        occurred_before = len(past_anomalies) > 0
        
        if not occurred_before:
            return {
                "has_occurred_before": False,
                "frequency": 0,
                "historical_severity_avg": 0.0,
                "average_recovery_days": 0.0
            }
            
        # 2. Similarity analysis
        # Find the past anomaly that is closest in percentage change and severity
        nearest_anomaly = None
        best_similarity = 0.0
        
        for pa in past_anomalies:
            sev_diff = abs(pa["severity"] - current_severity)
            chg_diff = abs(pa["percentage_change"] - current_change_pct)
            
            # Distance metric: similarity score from 0 to 1
            distance = np.sqrt((sev_diff / 100.0)**2 + (chg_diff / 100.0)**2)
            similarity = max(0.0, 1.0 - distance)
            
            if similarity > best_similarity:
                best_similarity = similarity
                nearest_anomaly = pa
                
        avg_recovery = float(np.mean(recovery_times)) if recovery_times else 1.0
        max_severity = float(np.max([pa["severity"] for pa in past_anomalies]))
        
        return {
            "has_occurred_before": True,
            "frequency": len(past_anomalies),
            "historical_severity_avg": round(float(np.mean([pa["severity"] for pa in past_anomalies])), 2),
            "max_historical_severity": round(max_severity, 2),
            "average_recovery_days": round(avg_recovery, 1),
            "similarity_score": round(best_similarity, 4),
            "nearest_historical_anomaly": {
                "date": nearest_anomaly["date"],
                "actual": round(nearest_anomaly["actual"], 4),
                "prediction": round(nearest_anomaly["prediction"], 4),
                "residual": round(nearest_anomaly["residual"], 4),
                "percentage_change": round(nearest_anomaly["percentage_change"], 2),
                "severity_score": round(nearest_anomaly["severity"], 2)
            } if nearest_anomaly else None
        }

    def monitor_forecast_accuracy(
        self,
        df_actual: pd.DataFrame,
        df_forecast: pd.DataFrame,
        product_id: str,
        kpi: str,
        lookback_days: int = 30
    ) -> Dict[str, Any]:
        """
        Monitors ongoing forecast accuracy (Layer 11) for a KPI by comparing actual vs. predicted values.
        """
        kpi_lower = kpi.lower()
        act_prod = df_actual[df_actual["product_id"] == product_id].copy()
        for_prod = df_forecast[df_forecast["product_id"] == product_id].copy()
        
        if len(act_prod) == 0 or len(for_prod) == 0:
            return {"status": "No forecast data available"}
            
        act_prod["date"] = pd.to_datetime(act_prod["date"])
        for_prod["date"] = pd.to_datetime(for_prod["date"])
        
        merged = pd.merge(
            act_prod, for_prod, on="date", suffixes=("_act", "_pred")
        ).sort_values(by="date")
        
        history = merged.tail(lookback_days)
        if len(history) == 0:
            return {"status": "No historical overlap found"}
            
        act = history[f"{kpi_lower}_act"].values
        pred = history[f"{kpi_lower}_pred"].values
        
        mape = float(np.mean(np.abs((act - pred) / (act + 1e-5))) * 100.0)
        rmse = float(np.sqrt(np.mean((act - pred)**2)))
        bias = float(np.mean(act - pred))
        
        return {
            "evaluation_period_days": len(history),
            "mape_pct": round(mape, 2),
            "rmse": round(rmse, 4),
            "system_bias": "Underpredicting" if bias > 0 else "Overpredicting",
            "mean_absolute_bias": round(abs(bias), 4)
        }
