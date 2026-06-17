import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.covariance import EllipticEnvelope

class MultivariateAnomalyDetector:
    def __init__(self, algorithm: str = "mahalanobis", contamination: float = 0.05):
        self.algorithm = algorithm.lower()
        self.contamination = contamination
        self.feature_cols = [
            "traffic", "marketing_spend", "inventory_available", "avg_selling_price",
            "discount_pct", "current_ctr", "current_roas", "orders", "revenue",
            "profit", "conversion_rate", "retention_rate"
        ]

    def detect_multivariate(
        self,
        df: pd.DataFrame,
        product_id: str,
        target_date: str
    ) -> Dict[str, Any]:
        """
        Runs multivariate anomaly detection on a target day relative to historical combinations.
        """
        # Filter product history
        prod_df = df[df["product_id"] == product_id].copy()
        prod_df["date"] = pd.to_datetime(prod_df["date"])
        prod_df = prod_df.sort_values(by="date")
        
        # Ensure target date is in the dataframe
        target_ts = pd.to_datetime(target_date)
        target_row = prod_df[prod_df["date"] == target_ts]
        
        if len(target_row) == 0:
            return {
                "anomaly_detected": False,
                "reason": f"Target date {target_date} not found in dataset"
            }
            
        # Keep numeric cols only
        history_df = prod_df[prod_df["date"] < target_ts].copy()
        
        if len(history_df) < 15:
            return {
                "anomaly_detected": False,
                "reason": "Insufficient historical context to fit multivariate model"
            }
            
        # Select features
        X_hist = history_df[self.feature_cols].fillna(0.0).values
        X_target = target_row[self.feature_cols].fillna(0.0).values[0]
        
        # Calculate statistics
        if self.algorithm == "mahalanobis":
            return self._detect_mahalanobis(X_hist, X_target)
        elif self.algorithm == "isolation_forest":
            return self._detect_isolation_forest(X_hist, X_target)
        elif self.algorithm == "lof":
            return self._detect_lof(X_hist, X_target)
        elif self.algorithm == "robust_covariance":
            return self._detect_robust_covariance(X_hist, X_target)
        else:
            return self._detect_mahalanobis(X_hist, X_target)

    def _detect_mahalanobis(self, X_hist: np.ndarray, x: np.ndarray) -> Dict[str, Any]:
        """
        Mahalanobis Distance anomaly detection with feature attribution.
        """
        mean_vec = np.mean(X_hist, axis=0)
        cov_matrix = np.cov(X_hist, rowvar=False)
        
        # Regularize covariance if it is singular
        if np.linalg.cond(cov_matrix) > 1e12 or np.linalg.det(cov_matrix) == 0:
            cov_matrix += np.eye(cov_matrix.shape[0]) * 1e-4
            
        cov_inv = np.linalg.pinv(cov_matrix)
        
        diff = x - mean_vec
        m_dist_sq = diff.T @ cov_inv @ diff
        m_dist = np.sqrt(max(0.0, m_dist_sq))
        
        # Calculate historical distance distribution to get z-score and probability
        hist_dists = []
        for row in X_hist:
            d = row - mean_vec
            hist_dists.append(np.sqrt(max(0.0, d.T @ cov_inv @ d)))
            
        dist_mean = np.mean(hist_dists)
        dist_std = np.std(hist_dists) if np.std(hist_dists) > 0 else 1.0
        
        z_score = (m_dist - dist_mean) / dist_std
        
        # Anomaly threshold: 95th percentile or z-score > 2.0
        anomaly_detected = bool(z_score > 2.0)
        anomaly_score = min(100.0, max(0.0, z_score * 25.0)) # Z-score 4 -> 100
        
        # Calculate feature contributions
        # Component contribution: diff_i * sum_j (cov_inv_ij * diff_j)
        contribs = diff * (cov_inv @ diff)
        contrib_pct = {}
        for idx, col in enumerate(self.feature_cols):
            contrib_pct[col] = float(contribs[idx] / (m_dist_sq + 1e-5))
            
        # Normalize contributions
        sum_contrib = sum(abs(v) for v in contrib_pct.values()) or 1.0
        sorted_contribs = []
        for col, val in contrib_pct.items():
            sorted_contribs.append({
                "feature": col,
                "contribution_pct": round(abs(val) / sum_contrib * 100.0, 2),
                "direction": "above baseline" if x[self.feature_cols.index(col)] > mean_vec[self.feature_cols.index(col)] else "below baseline"
            })
        sorted_contribs = sorted(sorted_contribs, key=lambda x: x["contribution_pct"], reverse=True)
        
        # Nearest normal observation
        nearest_obs = self._get_nearest_observation(X_hist, x)
        
        return {
            "anomaly_detected": anomaly_detected,
            "anomaly_score": round(anomaly_score, 2),
            "algorithm": "Mahalanobis Distance",
            "distance": round(float(m_dist), 4),
            "z_score": round(float(z_score), 4),
            "feature_contributions": sorted_contribs[:5],
            "nearest_normal_observation": nearest_obs
        }

    def _detect_isolation_forest(self, X_hist: np.ndarray, x: np.ndarray) -> Dict[str, Any]:
        """
        Isolation Forest anomaly detection.
        """
        clf = IsolationForest(contamination=self.contamination, random_state=42)
        clf.fit(X_hist)
        
        pred = clf.predict(x.reshape(1, -1))[0]
        score = clf.score_samples(x.reshape(1, -1))[0]
        
        # Normalize score into 0-100 range
        # Isolation Forest score returns values around [-0.8, -0.2], lower is more anomalous
        # Normalize so that lower scores translate to higher anomaly score
        norm_score = float((0.7 + score) / 0.5) if score < -0.3 else 0.0
        anomaly_score = min(100.0, max(0.0, norm_score * 100.0))
        
        # Feature contributions via mean difference
        sorted_contribs = self._get_baseline_contributions(X_hist, x)
        nearest_obs = self._get_nearest_observation(X_hist, x)
        
        return {
            "anomaly_detected": bool(pred == -1),
            "anomaly_score": round(anomaly_score, 2),
            "algorithm": "Isolation Forest",
            "decision_score": round(float(score), 4),
            "feature_contributions": sorted_contribs[:5],
            "nearest_normal_observation": nearest_obs
        }

    def _detect_lof(self, X_hist: np.ndarray, x: np.ndarray) -> Dict[str, Any]:
        """
        Local Outlier Factor (LOF) anomaly detection.
        """
        clf = LocalOutlierFactor(contamination=self.contamination, novelty=True)
        clf.fit(X_hist)
        
        pred = clf.predict(x.reshape(1, -1))[0]
        score = clf.decision_function(x.reshape(1, -1))[0]
        
        anomaly_score = min(100.0, max(0.0, (score * -1.0 + 0.5) * 100.0)) if score < 0 else 0.0
        
        # Baseline difference attribution
        sorted_contribs = self._get_baseline_contributions(X_hist, x)
        nearest_obs = self._get_nearest_observation(X_hist, x)
        
        return {
            "anomaly_detected": bool(pred == -1),
            "anomaly_score": round(anomaly_score, 2),
            "algorithm": "Local Outlier Factor",
            "decision_score": round(float(score), 4),
            "feature_contributions": sorted_contribs[:5],
            "nearest_normal_observation": nearest_obs
        }

    def _detect_robust_covariance(self, X_hist: np.ndarray, x: np.ndarray) -> Dict[str, Any]:
        """
        Elliptic Envelope (Robust Covariance) anomaly detection.
        """
        clf = EllipticEnvelope(contamination=self.contamination, random_state=42)
        clf.fit(X_hist)
        
        pred = clf.predict(x.reshape(1, -1))[0]
        score = clf.decision_function(x.reshape(1, -1))[0]
        
        anomaly_score = min(100.0, max(0.0, (score * -1.0 + 0.5) * 100.0)) if score < 0 else 0.0
        
        # Attribution
        sorted_contribs = self._get_baseline_contributions(X_hist, x)
        nearest_obs = self._get_nearest_observation(X_hist, x)
        
        return {
            "anomaly_detected": bool(pred == -1),
            "anomaly_score": round(anomaly_score, 2),
            "algorithm": "Robust Covariance",
            "decision_score": round(float(score), 4),
            "feature_contributions": sorted_contribs[:5],
            "nearest_normal_observation": nearest_obs
        }

    def _get_nearest_observation(self, X_hist: np.ndarray, x: np.ndarray) -> Dict[str, float]:
        nearest_idx = np.argmin(np.linalg.norm(X_hist - x, axis=1))
        return {col: float(val) for col, val in zip(self.feature_cols, X_hist[nearest_idx])}

    def _get_baseline_contributions(self, X_hist: np.ndarray, x: np.ndarray) -> List[Dict[str, Any]]:
        mean_vec = np.mean(X_hist, axis=0)
        diff = np.abs(x - mean_vec) / (np.std(X_hist, axis=0) + 1e-5)
        sorted_contribs = []
        for idx, col in enumerate(self.feature_cols):
            sorted_contribs.append({
                "feature": col,
                "contribution_pct": round(diff[idx] / (np.sum(diff) + 1e-5) * 100.0, 2),
                "direction": "above baseline" if x[idx] > mean_vec[idx] else "below baseline"
            })
        return sorted(sorted_contribs, key=lambda x: x["contribution_pct"], reverse=True)
