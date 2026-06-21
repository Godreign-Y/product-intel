import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from src.core.forecaster import ProductForecaster
from src.core.explainer import PredictionExplainer
from src.utils.logger import setup_logger

from src.core.anomaly.residual import ResidualAnomalyDetector
from src.core.anomaly.rolling import RollingTrendDetector
from src.core.anomaly.changepoint import ChangePointDetector
from src.core.anomaly.multivariate import MultivariateAnomalyDetector
from src.core.anomaly.rules import BusinessRuleEngine
from src.core.anomaly.relations import KPIRelationshipMonitor
from src.core.anomaly.explain import AnomalyExplainer
from src.core.anomaly.severity import SeverityScorer
from src.core.anomaly.impact import BusinessImpactEstimator
from src.core.anomaly.history import HistoricalAnomalyContext
from src.core.anomaly.ranking import ProductAnomalyRanker

logger = setup_logger("anomaly_engine")

class AnomalyDetectionEngine:
    def __init__(
        self,
        forecaster: ProductForecaster,
        explainer: PredictionExplainer,
        df_historical: Optional[pd.DataFrame] = None
    ):
        self.forecaster = forecaster
        self.explainer = explainer
        self.df_historical = df_historical
        
        # Instantiate sub-analyzers
        self.residual_detector = ResidualAnomalyDetector(forecaster.step_residuals)
        self.trend_detector = RollingTrendDetector()
        self.cp_detector = ChangePointDetector()
        self.mv_detector = MultivariateAnomalyDetector()
        self.rule_engine = BusinessRuleEngine()
        self.relation_monitor = KPIRelationshipMonitor()
        self.anomaly_explainer = AnomalyExplainer(explainer)
        self.severity_scorer = SeverityScorer()
        self.impact_estimator = BusinessImpactEstimator()
        self.history_context = HistoricalAnomalyContext()
        self.ranker = ProductAnomalyRanker()
        
        # In-memory caches for performance optimization
        self._detection_cache = {}
        self._ranking_cache = {}

    def run_detection(
        self,
        product_id: str,
        target_date: Optional[str] = None,
        kpi: str = "revenue",
        skip_explanation: bool = False
    ) -> Dict[str, Any]:
        """
        Runs the full 15-layer anomaly detection pipeline for a single product KPI on a target date.
        """
        kpi_lower = kpi.lower()
        
        df_hist = self.df_historical
        if df_hist is None:
            from src.api.dependencies import get_historical_df_from_db
            df_hist = get_historical_df_from_db(product_id=product_id)
            
        prod_data = df_hist[df_hist["product_id"] == product_id].copy()
        if len(prod_data) == 0:
            return {"error": f"Product ID {product_id} not found in historical dataset."}
            
        prod_data["date"] = pd.to_datetime(prod_data["date"])
        prod_data = prod_data.sort_values(by="date").reset_index(drop=True)

        if target_date is None:
            target_ts = prod_data["date"].max()
            target_date = target_ts.strftime("%Y-%m-%d")
        else:
            target_ts = pd.to_datetime(target_date)
            
        cache_key = (product_id, target_date, kpi_lower)
        if hasattr(self, "_detection_cache") and cache_key in self._detection_cache:
            cached_res = self._detection_cache[cache_key]
            # Only return from cache if it contains explanations, OR if we are skipping them anyway
            if skip_explanation or (cached_res.get("explanation") and len(cached_res["explanation"].get("top_drivers", [])) > 0):
                return cached_res
            
        target_rows = prod_data[prod_data["date"] == target_ts]
        if len(target_rows) == 0:
            return {"error": f"Target date {target_date} not found for product {product_id}."}
            
        target_row = target_rows.iloc[0]
        actual_val = float(target_row[kpi_lower])
        
        # Slice historical dataset up to preceding day
        hist_before = prod_data[prod_data["date"] < target_ts].copy()
        if len(hist_before) < 10:
            return {"error": f"Insufficient historical data prior to {target_date}."}
            
        # Run 1-step forecast for target day using prior day history
        forecast_df = self.forecaster.forecast(
            historical_df=df_hist,
            product_id=product_id,
            horizon_days=1,
            current_features={
                "avg_selling_price": float(hist_before["avg_selling_price"].iloc[-1]),
                "discount_pct": float(hist_before["discount_pct"].iloc[-1]),
                "shipping_fee": float(hist_before["shipping_fee"].iloc[-1]),
                "marketing_spend": float(hist_before["marketing_spend"].iloc[-1]),
                "inventory_available": float(hist_before["inventory_available"].iloc[-1]),
                "traffic": float(hist_before["traffic"].iloc[-1])
            }
        )
        # Ensure date is matching target
        forecast_df["date"] = target_ts
        pred_val = float(forecast_df[kpi_lower].iloc[0])
        
        # Merge actual slice with forecasted slice for detectors
        df_actual_single = prod_data[prod_data["date"] == target_ts].copy()
        
        # Layer 1: Residuals
        residuals_list = self.residual_detector.detect_residuals(
            df_actual=df_actual_single,
            df_forecast=forecast_df,
            product_id=product_id,
            target_metrics=[kpi_lower],
            window_type="daily"
        )
        if not residuals_list:
            return {"error": "Failed to calculate residuals."}
            
        res_info = residuals_list[0]["metrics"][kpi_lower]
        residual = res_info["residual"]
        pct_change = res_info["percentage_error"]
        z_score = res_info["z_score"]
        outside_ci = res_info["outside_ci"]
        
        # Layer 2: Rolling Trend
        trend_info = self.trend_detector.detect_trends(
            df=df_hist,
            product_id=product_id,
            metric=kpi_lower
        )
        # Get trend z-score from 30d or highest window
        win_keys = list(trend_info["windows"].keys())
        trend_z = trend_info["windows"][win_keys[-1]]["trend_z_score"] if win_keys else 0.0
        
        # Layer 3: Change Point
        cp_info = self.cp_detector.detect_change_points(
            df=df_hist,
            product_id=product_id,
            metric=kpi_lower
        )
        cp_detected = cp_info.get("change_point_detected", False)
        cp_conf = cp_info.get("confidence", 0.0) if cp_detected else 0.0
        
        # Layer 4: Multivariate Anomaly Detection
        mv_info = self.mv_detector.detect_multivariate(
            df=df_hist,
            product_id=product_id,
            target_date=target_date
        )
        mv_score = mv_info.get("anomaly_score", 0.0)
        
        # Layer 5: Business Rules
        rules_triggered = self.rule_engine.evaluate_rules(
            df=df_hist,
            product_id=product_id,
            target_date=target_date
        )
        
        # Layer 6: Relationships
        relations_triggered = self.relation_monitor.monitor_relationships(
            df=df_hist,
            product_id=product_id,
            target_date=target_date
        )
        
        # Layer 8: Severity Scorer
        sev_info = self.severity_scorer.calculate_severity(
            residual_z_score=z_score,
            trend_z_score=trend_z,
            multivariate_score=mv_score,
            triggered_rules=rules_triggered,
            broken_relations=relations_triggered,
            change_point_confidence=cp_conf
        )
        
        # Layer 9: Business Impact
        avg_price = float(target_row.get("avg_selling_price", 0.0))
        traffic_val = float(target_row.get("traffic", 0.0))
        impact_info = self.impact_estimator.estimate_impact(
            kpi=kpi_lower,
            residual=residual,
            percentage_change=pct_change,
            avg_selling_price=avg_price,
            traffic=traffic_val,
            severity_status=sev_info["status"]
        )
        
        # Layer 10: Historical Context
        history_info = self.history_context.evaluate_historical_context(
            df_actual=df_hist,
            df_forecast=df_hist, # Evaluate on overall actuals for past accuracy
            product_id=product_id,
            kpi=kpi_lower,
            current_date=target_date,
            current_severity=sev_info["severity_score"],
            current_change_pct=pct_change
        )
        
        # Layer 11: Accuracy Monitoring
        accuracy_info = self.history_context.monitor_forecast_accuracy(
            df_actual=df_hist,
            df_forecast=df_hist,
            product_id=product_id,
            kpi=kpi_lower
        )
        
        # Layer 7 & 14: Explanations
        if not skip_explanation:
            explain_info = self.anomaly_explainer.explain_anomaly(
                historical_df=df_hist,
                product_id=product_id,
                target_date=target_date,
                kpi=kpi_lower,
                expected=pred_val,
                actual=actual_val,
                residual=residual,
                percentage_change=pct_change,
                triggered_rules=rules_triggered,
                broken_relations=relations_triggered
            )
        else:
            explain_info = {
                "anomaly_kpi": kpi.title(),
                "expected_value": round(pred_val, 4),
                "actual_value": round(actual_val, 4),
                "residual": round(residual, 4),
                "percentage_change": round(pct_change, 2),
                "business_explanation": "",
                "top_drivers": [],
                "triggered_rules_summary": [],
                "broken_relations_summary": [],
                "recommended_actions": []
            }
        
        # Layer 15: Structured JSON formatting
        result = {
            "product_id": product_id,
            "target_date": target_date,
            "kpi": kpi.upper(),
            "expected_value": round(pred_val, 4),
            "actual_value": round(actual_val, 4),
            "residual": round(residual, 4),
            "percentage_change": round(pct_change, 2),
            "severity_score": sev_info["severity_score"],
            "status": sev_info["status"],
            "change_point_detected": cp_detected,
            "change_point_details": cp_info,
            "multivariate_details": mv_info,
            "business_rules_triggered": rules_triggered,
            "broken_relations": relations_triggered,
            "business_impact": impact_info,
            "historical_context": history_info,
            "forecast_monitoring": accuracy_info,
            "explanation": explain_info,
            "confidence_interval_95": res_info["confidence_interval_95"],
            "outside_ci": outside_ci,
            "trend_details": trend_info
        }
        if hasattr(self, "_detection_cache"):
            existing = self._detection_cache.get(cache_key)
            # Only cache if we calculated explanations, OR if there's no existing full version cached
            if not skip_explanation or not existing:
                self._detection_cache[cache_key] = result
        return result

    def detect_category_anomalies(self, category: str, date: Optional[str] = None, kpi: str = "revenue") -> List[Dict[str, Any]]:
        """
        Runs anomaly detection across all products within a specific category.
        """
        df_hist = self.df_historical
        if df_hist is None:
            from src.api.dependencies import get_historical_df_from_db
            df_hist = get_historical_df_from_db(category=category)
            
        if date is None:
            cat_df = df_hist[df_hist["category"] == category].copy()
            if len(cat_df) > 0:
                cat_df["date"] = pd.to_datetime(cat_df["date"])
                date = cat_df["date"].max().strftime("%Y-%m-%d")
            else:
                return []

        original_df = self.df_historical
        self.df_historical = df_hist
        try:
            prod_ids = df_hist[df_hist["category"] == category]["product_id"].unique()
            category_anomalies = []
            for prod_id in prod_ids:
                res = self.run_detection(product_id=prod_id, target_date=date, kpi=kpi)
                if "error" not in res:
                    category_anomalies.append(res)
            return category_anomalies
        finally:
            self.df_historical = original_df

    def get_top_products(self, date: Optional[str] = None, kpi: str = "revenue") -> Dict[str, Any]:
        """
        Generates global anomaly ranking and risk profiles across all products for a specific date.
        """
        df_hist = self.df_historical
        if df_hist is None:
            from src.api.dependencies import get_historical_df_from_db
            df_hist = get_historical_df_from_db()
            
        if date is None:
            df_hist_copy = df_hist.copy()
            df_hist_copy["date"] = pd.to_datetime(df_hist_copy["date"])
            date = df_hist_copy["date"].max().strftime("%Y-%m-%d")

        cache_key = (date, kpi.lower())
        if hasattr(self, "_ranking_cache") and cache_key in self._ranking_cache:
            return self._ranking_cache[cache_key]
            
        original_df = self.df_historical
        self.df_historical = df_hist
        try:
            unique_prods = df_hist["product_id"].unique()
            all_reports = []
            
            for prod_id in unique_prods:
                res = self.run_detection(product_id=prod_id, target_date=date, kpi=kpi, skip_explanation=True)
                if "error" not in res:
                    all_reports.append(res)
                    
            result = self.ranker.rank_products(all_reports)
            if hasattr(self, "_ranking_cache"):
                self._ranking_cache[cache_key] = result
            return result
        finally:
            self.df_historical = original_df

    def scan_anomalies(
        self,
        product_id: str,
        lookback_days: int = 14,
        kpi: str = "revenue"
    ) -> Dict[str, Any]:
        """
        Scans the past `lookback_days` days in the time series for the given product,
        detects anomalies on each day, and returns a summary of anomalous events.
        """
        df_hist = self.df_historical
        if df_hist is None:
            from src.api.dependencies import get_historical_df_from_db
            df_hist = get_historical_df_from_db(product_id=product_id)
            
        prod_data = df_hist[df_hist["product_id"] == product_id].copy()
        if len(prod_data) == 0:
            return {"error": f"Product ID {product_id} not found."}
            
        prod_data["date"] = pd.to_datetime(prod_data["date"])
        prod_data = prod_data.sort_values(by="date").reset_index(drop=True)
        
        # Get the range of dates to scan: the last `lookback_days` in the dataset
        latest_date = prod_data["date"].max()
        start_date = latest_date - pd.Timedelta(days=lookback_days - 1)
        
        scan_dates = prod_data[(prod_data["date"] >= start_date) & (prod_data["date"] <= latest_date)]["date"].tolist()
        
        anomalous_dates = []
        for date_ts in scan_dates:
            date_str = date_ts.strftime("%Y-%m-%d")
            res = self.run_detection(product_id=product_id, target_date=date_str, kpi=kpi, skip_explanation=True)
            if "error" not in res:
                if res["status"] in ["warning", "high", "critical"] or res["severity_score"] >= 35.0:
                    anomalous_dates.append({
                        "date": date_str,
                        "severity_score": res["severity_score"],
                        "status": res["status"],
                        "actual_value": res["actual_value"],
                        "expected_value": res["expected_value"],
                        "percentage_change": res["percentage_change"],
                        "residual": res["residual"]
                    })
                    
        return {
            "product_id": product_id,
            "lookback_days": lookback_days,
            "kpi": kpi.upper(),
            "anomalous_dates": anomalous_dates
        }
