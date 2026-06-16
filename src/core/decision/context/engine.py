import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Dict, Any, List

from src.core.history.storage.models import Snapshot, Event

class ContextEngine:
    def __init__(self, db: Session):
        self.db = db

    def get_latest_kpis(self) -> Dict[str, Any]:
        """
        Retrieves the most recent daily KPI snapshot averages.
        """
        latest = self.db.query(Snapshot).order_by(desc(Snapshot.snapshot_date)).first()
        if not latest:
            return {
                "total_revenue": 0.0,
                "total_profit": 0.0,
                "total_orders": 0,
                "mean_conversion_rate": 0.0,
                "mean_retention_rate": 0.0,
                "avg_discount_pct": 0.0,
                "avg_price": 0.0
            }
        
        return {
            "total_revenue": latest.total_revenue,
            "total_profit": latest.total_profit,
            "total_orders": latest.total_orders,
            "mean_conversion_rate": latest.mean_conversion_rate,
            "mean_retention_rate": latest.mean_retention_rate,
            "avg_discount_pct": latest.avg_discount_pct,
            "avg_price": latest.avg_price,
            "channel_mix": latest.channel_mix,
            "campaign_mix": latest.campaign_mix
        }

    def get_recent_anomalies(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieves recent statistical anomalies and outlier events.
        """
        events = self.db.query(Event).filter(
            Event.severity.in_(["High", "Critical"])
        ).order_by(desc(Event.event_date)).limit(limit).all()
        
        return [
            {
                "date": str(e.event_date),
                "product_id": e.product_id,
                "event_type": e.event_type,
                "severity": e.severity,
                "kpis_affected": e.kpis_affected,
                "reason": e.reason
            }
            for e in events
        ]

    def get_rolling_trends(self, days: int = 30) -> Dict[str, Any]:
        """
        Calculates simple linear growth indicators for revenue and orders.
        """
        snapshots = self.db.query(Snapshot).order_by(desc(Snapshot.snapshot_date)).limit(days).all()
        if len(snapshots) < 2:
            return {"revenue_growth_trend": "stable", "order_growth_trend": "stable"}
            
        snapshots = list(reversed(snapshots))
        first_half = snapshots[:len(snapshots)//2]
        second_half = snapshots[len(snapshots)//2:]
        
        avg_rev_first = sum(s.total_revenue for s in first_half) / len(first_half)
        avg_rev_second = sum(s.total_revenue for s in second_half) / len(second_half)
        
        avg_ord_first = sum(s.total_orders for s in first_half) / len(first_half)
        avg_ord_second = sum(s.total_orders for s in second_half) / len(second_half)
        
        rev_change = (avg_rev_second - avg_rev_first) / max(1.0, avg_rev_first)
        ord_change = (avg_ord_second - avg_ord_first) / max(1.0, avg_ord_first)
        
        return {
            "revenue_growth_pct": round(rev_change * 100.0, 2),
            "order_growth_pct": round(ord_change * 100.0, 2),
            "revenue_trend": "increasing" if rev_change > 0.02 else "decreasing" if rev_change < -0.02 else "stable",
            "order_trend": "increasing" if ord_change > 0.02 else "decreasing" if ord_change < -0.02 else "stable"
        }

    def assemble_context(self, query: str) -> Dict[str, Any]:
        """
        Compiles the complete business context object based on the user's intent.
        """
        return {
            "query": query,
            "kpis": self.get_latest_kpis(),
            "anomalies": self.get_recent_anomalies(),
            "trends": self.get_rolling_trends(),
            "assembled_at": datetime.datetime.utcnow().isoformat()
        }
