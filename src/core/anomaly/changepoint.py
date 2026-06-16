import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple

class ChangePointDetector:
    def __init__(self, algorithm: str = "cusum", config: Optional[Dict[str, Any]] = None):
        self.algorithm = algorithm.lower()
        self.config = config or {}

    def detect_change_points(
        self,
        df: pd.DataFrame,
        product_id: str,
        metric: str
    ) -> Dict[str, Any]:
        """
        Detects structural shifts in the given time series.
        """
        metric_lower = metric.lower()
        prod_data = df[df["product_id"] == product_id].copy()
        
        if len(prod_data) < 15:
            return {
                "change_point_detected": False,
                "reason": "Insufficient data points"
            }
            
        prod_data["date"] = pd.to_datetime(prod_data["date"])
        prod_data = prod_data.sort_values(by="date").reset_index(drop=True)
        
        dates = prod_data["date"].values
        values = prod_data[metric_lower].values
        
        if self.algorithm == "cusum":
            return self._detect_cusum(values, dates)
        elif self.algorithm == "adwin":
            return self._detect_adwin(values, dates)
        elif self.algorithm == "ruptures" or self.algorithm == "bayesian":
            return self._detect_bayesian_split(values, dates)
        else:
            # Fallback to CUSUM
            return self._detect_cusum(values, dates)

    def _detect_cusum(self, values: np.ndarray, dates: np.ndarray) -> Dict[str, Any]:
        """
        Cumulative Sum (CUSUM) change point detection.
        """
        mu = np.mean(values)
        std = np.std(values) if np.std(values) > 0 else 1.0
        
        # Slack parameter K (typically 0.5 * std of change we want to detect)
        K = self.config.get("cusum_k", 0.5) * std
        # Decision interval threshold H (typically 4-5 * std)
        H = self.config.get("cusum_h", 4.0) * std
        
        S_pos = np.zeros(len(values))
        S_neg = np.zeros(len(values))
        
        detected_idx = -1
        
        for i in range(1, len(values)):
            S_pos[i] = max(0.0, S_pos[i-1] + values[i] - mu - K)
            S_neg[i] = max(0.0, S_neg[i-1] - values[i] + mu - K)
            
            if S_pos[i] > H or S_neg[i] > H:
                detected_idx = i
                break
                
        if detected_idx != -1:
            return self._compile_stats(values, dates, detected_idx, "CUSUM")
            
        return {"change_point_detected": False, "algorithm": "CUSUM"}

    def _detect_adwin(self, values: np.ndarray, dates: np.ndarray) -> Dict[str, Any]:
        """
        Adaptive Windowing (ADWIN) change point detection.
        """
        delta = self.config.get("adwin_delta", 0.05)
        window = []
        detected_idx = -1
        
        for idx, val in enumerate(values):
            window.append(val)
            n = len(window)
            
            # Check all possible split points
            for t in range(2, n - 2):
                w1 = window[:t]
                w2 = window[t:]
                
                n1, n2 = len(w1), len(w2)
                mu1, mu2 = np.mean(w1), np.mean(w2)
                
                # Harmonic mean
                m = 1.0 / (1.0 / n1 + 1.0 / n2)
                eps = np.sqrt((1.0 / (2.0 * m)) * np.log(4.0 * n / delta))
                
                if abs(mu1 - mu2) > eps:
                    detected_idx = idx
                    # Trim window up to the split point
                    window = window[t:]
                    break
            
            if detected_idx != -1 and idx > 15: # Ensure we have some history
                break
                
        if detected_idx != -1:
            return self._compile_stats(values, dates, t, "ADWIN")
            
        return {"change_point_detected": False, "algorithm": "ADWIN"}

    def _detect_bayesian_split(self, values: np.ndarray, dates: np.ndarray) -> Dict[str, Any]:
        """
        Bayesian / SSE Split Point detection (minimizing Sum of Squared Errors).
        """
        n = len(values)
        best_sse = np.inf
        best_t = -1
        
        # Search for optimal split point minimizing within-segment variance
        for t in range(5, n - 5):
            seg1 = values[:t]
            seg2 = values[t:]
            
            sse = np.sum((seg1 - np.mean(seg1))**2) + np.sum((seg2 - np.mean(seg2))**2)
            if sse < best_sse:
                best_sse = sse
                best_t = t
                
        if best_t != -1:
            # Check statistical significance of mean shift
            seg1 = values[:best_t]
            seg2 = values[best_t:]
            mu1, mu2 = np.mean(seg1), np.mean(seg2)
            std1, std2 = np.std(seg1), np.std(seg2)
            
            # t-statistic proxy
            combined_std = np.sqrt((std1**2 / len(seg1)) + (std2**2 / len(seg2)))
            if combined_std > 0:
                t_stat = abs(mu1 - mu2) / combined_std
            else:
                t_stat = 0.0
                
            # If shift is significant (t_stat > 2.58, approx 99% confidence)
            if t_stat > 2.58:
                return self._compile_stats(values, dates, best_t, "Bayesian Split")
                
        return {"change_point_detected": False, "algorithm": "Bayesian Split"}

    def _compile_stats(self, values: np.ndarray, dates: np.ndarray, idx: int, algo: str) -> Dict[str, Any]:
        before_seq = values[:idx]
        after_seq = values[idx:]
        
        before_mean = float(np.mean(before_seq))
        after_mean = float(np.mean(after_seq))
        before_var = float(np.var(before_seq))
        after_var = float(np.var(after_seq))
        
        magnitude = after_mean - before_mean
        pct_change = (magnitude / (before_mean + 1e-5)) * 100.0
        
        # Simple confidence calculation based on mean difference vs std error
        comb_std = np.sqrt((before_var / len(before_seq)) + (after_var / len(after_seq)))
        confidence = min(1.0, max(0.0, abs(magnitude) / (comb_std * 3.0 + 1e-5)))
        
        date_str = pd.to_datetime(dates[idx]).strftime("%Y-%m-%d")
        
        return {
            "change_point_detected": True,
            "algorithm": algo,
            "change_point_date": date_str,
            "index": int(idx),
            "magnitude": round(magnitude, 4),
            "percentage_change": round(pct_change, 2),
            "confidence": round(confidence, 4),
            "before_mean": round(before_mean, 4),
            "after_mean": round(after_mean, 4),
            "before_variance": round(before_var, 4),
            "after_variance": round(after_var, 4)
        }
