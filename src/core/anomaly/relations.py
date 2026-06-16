import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from scipy.stats import pearsonr, spearmanr
from sklearn.feature_selection import mutual_info_regression

class KPIRelationshipMonitor:
    def __init__(self):
        # Pairs to monitor
        self.kpi_pairs = [
            ("traffic", "orders", "Traffic to Orders"),
            ("orders", "revenue", "Orders to Revenue"),
            ("revenue", "profit", "Revenue to Profit"),
            ("marketing_spend", "traffic", "Marketing Spend to Traffic"),
            ("current_ctr", "conversion_rate", "CTR to Conversion Rate")
        ]

    def monitor_relationships(
        self,
        df: pd.DataFrame,
        product_id: str,
        target_date: str,
        lookback_days: int = 40
    ) -> List[Dict[str, Any]]:
        """
        Monitors relationship correlations, elasticities, and drifts between KPIs.
        """
        prod_df = df[df["product_id"] == product_id].copy()
        prod_df["date"] = pd.to_datetime(prod_df["date"])
        prod_df = prod_df.sort_values(by="date").reset_index(drop=True)
        
        target_ts = pd.to_datetime(target_date)
        target_idx_list = prod_df[prod_df["date"] == target_ts].index.tolist()
        
        if not target_idx_list:
            return []
            
        idx = target_idx_list[0]
        
        # We need historical slice before target date to fit baseline correlations
        hist_slice = prod_df.iloc[max(0, idx - lookback_days):idx].copy()
        if len(hist_slice) < 10:
            return []
            
        target_row = prod_df.iloc[idx]
        prev_row = prod_df.iloc[idx - 1] if idx > 0 else target_row
        
        anomalous_relations = []
        
        for k1, k2, name in self.kpi_pairs:
            if k1 not in hist_slice.columns or k2 not in hist_slice.columns:
                continue
                
            x_hist = hist_slice[k1].fillna(0.0).values
            y_hist = hist_slice[k2].fillna(0.0).values
            
            # 1. Baseline Correlations
            p_corr, _ = pearsonr(x_hist, y_hist)
            s_corr, _ = spearmanr(x_hist, y_hist)
            
            # Avoid nan correlations
            if np.isnan(p_corr): p_corr = 0.0
            if np.isnan(s_corr): s_corr = 0.0
            
            # 2. Mutual Information
            try:
                mi = float(mutual_info_regression(x_hist.reshape(-1, 1), y_hist)[0])
            except Exception:
                mi = 0.0
                
            # 3. Check Target Day Movement vs. Historical Direction
            # If historical Pearson is positive, they should move together
            x_target, y_target = float(target_row[k1]), float(target_row[k2])
            x_prev, y_prev = float(prev_row[k1]), float(prev_row[k2])
            
            x_change = x_target - x_prev
            y_change = y_target - y_prev
            
            is_anomaly = False
            anomaly_type = "Normal"
            confidence = 0.0
            details = ""
            
            # If they are strongly positively correlated historically (e.g. Pearson > 0.4),
            # but moved in opposite directions on the target day.
            if p_corr > 0.4:
                # Expected: same sign changes
                if (x_change > 0.05 * x_prev and y_change < -0.05 * y_prev) or (x_change < -0.05 * x_prev and y_change > 0.05 * y_prev):
                    is_anomaly = True
                    anomaly_type = "Broken Positive Correlation"
                    confidence = float(min(1.0, abs(p_corr) * (abs(x_change) / (x_prev + 1e-5))))
                    details = f"Historically, {k1} and {k2} move together (Pearson = {p_corr:.2f}). On {target_date}, they diverged."
            
            # If they are strongly negatively correlated (Pearson < -0.4),
            # but moved in the same direction on the target day.
            elif p_corr < -0.4:
                if (x_change > 0.05 * x_prev and y_change > 0.05 * y_prev) or (x_change < -0.05 * x_prev and y_change < -0.05 * y_prev):
                    is_anomaly = True
                    anomaly_type = "Broken Negative Correlation"
                    confidence = float(min(1.0, abs(p_corr) * (abs(x_change) / (x_prev + 1e-5))))
                    details = f"Historically, {k1} and {k2} move inversely (Pearson = {p_corr:.2f}). On {target_date}, they moved in the same direction."
            
            # Unexpected elasticity: e.g., if Marketing increased by 50%, but Traffic stayed completely flat or dropped
            if k1 == "marketing_spend" and k2 == "traffic":
                if x_prev > 0:
                    marketing_increase = x_change / x_prev
                    if marketing_increase > 0.30 and y_change <= 0.0:
                        is_anomaly = True
                        anomaly_type = "Unexpected Elasticity (Flat Performance)"
                        confidence = 0.85
                        details = f"Marketing Spend increased by {marketing_increase*100:.1f}%, but Traffic decreased or stayed flat."
                        
            if is_anomaly:
                anomalous_relations.append({
                    "relationship_name": name,
                    "kpi_pair": [k1, k2],
                    "anomaly_type": anomaly_type,
                    "pearson_correlation": round(p_corr, 4),
                    "spearman_correlation": round(s_corr, 4),
                    "mutual_information": round(mi, 4),
                    "confidence": round(confidence, 4),
                    "details": details
                })
                
        return anomalous_relations
