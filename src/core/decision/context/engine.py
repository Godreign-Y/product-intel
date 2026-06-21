import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Dict, Any, List, Optional

from src.core.history.storage.models import Snapshot, Event, Pattern
from src.core.history.manager import HistoryManager
from src.core.decision.config_loader import load_decision_config
from src.utils.logger import setup_logger

logger = setup_logger("context_engine")

class ContextEngine:
    def __init__(self, db: Session, history_manager: Optional[HistoryManager] = None):
        self.db = db
        self.history_manager = history_manager or HistoryManager(db)
        cfg = load_decision_config()
        ctx_cfg = cfg.get("context", {})
        self.rolling_window = ctx_cfg.get("rolling_window_days", 7)
        self.trend_threshold = ctx_cfg.get("trend_threshold_pct", 0.02)
        logger.info(f"Initialized ContextEngine with rolling_window={self.rolling_window} days and trend_threshold={self.trend_threshold}")

    def get_latest_kpis(self, product_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieves core KPIs from HistoryManager get_kpi_snapshot.
        """
        prod_id = product_id or "P001"
        logger.debug(f"Fetching latest KPIs snapshot for product_id: {prod_id} over rolling window of {self.rolling_window} days")
        kpis = self.history_manager.get_kpi_snapshot(prod_id, self.rolling_window)
        logger.debug(f"Retrieved KPIs: {kpis}")
        return kpis

    def get_recent_anomalies(self, product_id: str = "P001", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieves recent anomalies for the product in the last 30 days using anomaly_detect.
        """
        import os
        from anomaly_detect.service import detect_anomalies
        
        dataset_path = "temporal_dataset.csv"
        if not os.path.exists(dataset_path):
            workspace_root = os.getcwd()
            dataset_path = os.path.join(workspace_root, "temporal_dataset.csv")
            if not os.path.exists(dataset_path):
                logger.warning(f"Temporal dataset not found at {dataset_path}. Returning empty anomalies list.")
                return []
                
        core_kpis = ["revenue", "profit", "orders", "conversion_rate"]
        all_anoms = []
        
        logger.info(f"Scanning for anomalies in dataset {dataset_path} for product_id: {product_id}")
        for kpi in core_kpis:
            try:
                logger.debug(f"Calling detect_anomalies for product_id: {product_id}, KPI: {kpi}")
                res = detect_anomalies(
                    file_path=dataset_path,
                    product_id=product_id,
                    kpi=kpi,
                    date_range="30 Days"
                )
                for point in res.anomalies:
                    severity = "High" if point.score >= 75.0 else "Medium" if point.score >= 50.0 else "Low"
                    all_anoms.append({
                        "date": point.date,
                        "kpi": kpi,
                        "value": point.value,
                        "score": point.score,
                        "anomaly_type": point.anomaly_type,
                        "deviation_pct": point.deviation_pct,
                        "status": point.status,
                        "severity": severity,
                        "description": f"{kpi.replace('_', ' ').title()} {point.anomaly_type.replace('_', ' ')} detected (Score: {point.score}, Deviation: {point.deviation_pct}%)"
                    })
            except Exception as e:
                logger.warning(f"Anomaly detection failed for KPI {kpi} on product {product_id}: {e}")
                pass
                
        # Sort anomalies by date descending (most recent first)
        all_anoms.sort(key=lambda x: x["date"], reverse=True)
        logger.info(f"Total anomalies detected for product {product_id} across core KPIs: {len(all_anoms)}")
        return all_anoms[:limit]

    def get_rolling_trends(self, product_id: str = "P001") -> Dict[str, Any]:
        """
        Retrieves pre-computed trend direction and percentage change from Pattern table.
        """
        logger.info(f"Fetching rolling trends from Pattern database for product_id: {product_id}")
        rev_trend = self.history_manager.get_trend_direction(product_id, "revenue")
        ord_trend = self.history_manager.get_trend_direction(product_id, "orders")
        
        rev_pct = 0.0
        ord_pct = 0.0
        
        p_rev = self.db.query(Pattern).filter(
            Pattern.pattern_type == "trend",
            Pattern.product_id == product_id,
            Pattern.kpi == "revenue"
        ).order_by(Pattern.date.desc()).first()
        
        if p_rev and p_rev.value is not None:
            rev_pct = round(p_rev.value * 100.0, 2)
            logger.debug(f"Found revenue pattern trend value: {rev_pct}%")
            
        p_ord = self.db.query(Pattern).filter(
            Pattern.pattern_type == "trend",
            Pattern.product_id == product_id,
            Pattern.kpi == "orders"
        ).order_by(Pattern.date.desc()).first()
        
        if p_ord and p_ord.value is not None:
            ord_pct = round(p_ord.value * 100.0, 2)
            logger.debug(f"Found orders pattern trend value: {ord_pct}%")
            
        trends = {
            "revenue_growth_pct": rev_pct,
            "order_growth_pct": ord_pct,
            "revenue_trend": rev_trend,
            "order_trend": ord_trend
        }
        logger.info(f"Calculated trends for product {product_id}: {trends}")
        return trends

    def assemble_context(self, query: str, product_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Compiles the complete business context object using pre-computed history profiles.
        """
        prod_id = product_id or "P001"
        logger.info(f"Assembling context query: '{query}' for product: {prod_id}")
        
        kpis = self.get_latest_kpis(prod_id)
        anoms = self.get_recent_anomalies(prod_id)
        trends = self.get_rolling_trends(prod_id)
        
        assembled = {
            "query": query,
            "product_id": prod_id,
            "kpis": kpis,
            "anomalies": anoms,
            "trends": trends,
            "assembled_at": datetime.datetime.utcnow().isoformat()
        }
        logger.info(f"Successfully assembled context for query '{query}'")
        return assembled
