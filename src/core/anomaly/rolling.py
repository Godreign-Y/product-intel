import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

class RollingTrendDetector:
    def __init__(self, windows: Optional[List[int]] = None):
        self.windows = windows or [7, 14, 30, 60]

    def detect_trends(
        self,
        df: pd.DataFrame,
        product_id: str,
        metric: str
    ) -> Dict[str, Any]:
        """
        Detects gradual performance degradation, growth, and volatility shifts across multiple windows.
        """
        metric_lower = metric.lower()
        prod_data = df[df["product_id"] == product_id].copy()
        
        if len(prod_data) < max(self.windows) + 10:
            return {
                "product_id": product_id,
                "metric": metric,
                "windows": {},
                "status": "Insufficient data"
            }
            
        prod_data["date"] = pd.to_datetime(prod_data["date"])
        prod_data = prod_data.sort_values(by="date").reset_index(drop=True)
        values = prod_data[metric_lower]
        
        results = {}
        flags = []
        
        for win in self.windows:
            if len(values) < win * 2:
                continue
                
            # Current Window: last 'win' rows
            current_win_vals = values.tail(win).values
            # Historical Baseline: all rows before last 'win' rows
            baseline_vals = values.iloc[:-win].values
            
            # 1. Base Rolling Statistics (Current Window)
            curr_mean = float(np.mean(current_win_vals))
            curr_median = float(np.median(current_win_vals))
            curr_std = float(np.std(current_win_vals))
            curr_var = float(np.var(current_win_vals))
            
            # Baseline Stats
            base_mean = float(np.mean(baseline_vals))
            base_std = float(np.std(baseline_vals)) if len(baseline_vals) > 1 else 1.0
            if base_std <= 0:
                base_std = 1e-5
                
            # 2. Trend Calculations
            pct_change = ((curr_mean - base_mean) / (base_mean + 1e-5)) * 100.0
            z_score = (curr_mean - base_mean) / base_std
            
            # Growth Rate within Current Window (first half vs second half)
            half = win // 2
            first_half_mean = float(np.mean(current_win_vals[:half]))
            second_half_mean = float(np.mean(current_win_vals[half:]))
            drift = second_half_mean - first_half_mean
            
            # Rolling Momentum: difference between end and start of current window
            momentum = float(current_win_vals[-1] - current_win_vals[0])
            
            # Growth Rate
            growth_rate = (drift / (first_half_mean + 1e-5)) * 100.0
            
            # Trend Confidence: ratio of positive daily changes inside the window
            daily_diffs = np.diff(current_win_vals)
            positive_days = np.sum(daily_diffs > 0)
            trend_confidence = float(positive_days / len(daily_diffs)) if len(daily_diffs) > 0 else 0.5
            
            # Determine Flags
            win_flags = []
            if z_score < -2.0 and growth_rate < -5.0:
                win_flags.append("persistent decline")
            elif z_score > 2.0 and growth_rate > 5.0:
                win_flags.append("persistent growth")
            elif z_score < -1.0 and abs(growth_rate) < 5.0:
                win_flags.append("slow degradation")
            elif z_score > 1.0 and abs(growth_rate) < 5.0:
                win_flags.append("slow improvement")
                
            # Instability: current variance is significantly higher than baseline variance
            base_var = float(np.var(baseline_vals)) if len(baseline_vals) > 1 else 1.0
            if base_var > 0 and (curr_var / base_var) > 2.0:
                win_flags.append("unstable period")
                
            results[win] = {
                "rolling_mean": round(curr_mean, 4),
                "rolling_median": round(curr_median, 4),
                "rolling_std": round(curr_std, 4),
                "rolling_variance": round(curr_var, 4),
                "growth_rate_pct": round(growth_rate, 2),
                "momentum": round(momentum, 4),
                "trend_z_score": round(z_score, 4),
                "percentage_change": round(pct_change, 2),
                "rolling_drift": round(drift, 4),
                "trend_confidence": round(trend_confidence, 4),
                "flags": win_flags
            }
            flags.extend([f"Window {win}d: {f}" for f in win_flags])
            
        return {
            "product_id": product_id,
            "metric": metric,
            "windows": results,
            "summary_flags": sorted(list(set(flags)))
        }
