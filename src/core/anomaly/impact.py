from typing import Dict, Any

class BusinessImpactEstimator:
    def __init__(self):
        pass

    def estimate_impact(
        self,
        kpi: str,
        residual: float,
        percentage_change: float,
        avg_selling_price: float,
        traffic: float,
        severity_status: str
    ) -> Dict[str, Any]:
        """
        Estimates the direct financial loss, projected losses, and recovery timelines for an anomaly.
        """
        kpi_lower = kpi.lower()
        
        # Losses are relevant only for negative anomalies (drops in metrics)
        is_loss = residual < 0
        
        current_revenue_loss = 0.0
        current_profit_loss = 0.0
        current_order_loss = 0.0
        
        if is_loss:
            abs_res = abs(residual)
            if kpi_lower == "revenue":
                current_revenue_loss = abs_res
                current_order_loss = abs_res / (avg_selling_price + 1e-5)
                # Assume average 15% profit margin if profit loss is not directly calculated
                current_profit_loss = current_revenue_loss * 0.15
            elif kpi_lower == "profit":
                current_profit_loss = abs_res
                current_revenue_loss = abs_res / 0.15 # Back-calculate revenue at 15% margin proxy
            elif kpi_lower == "orders":
                current_order_loss = abs_res
                current_revenue_loss = current_order_loss * avg_selling_price
                current_profit_loss = current_revenue_loss * 0.15
            elif kpi_lower == "conversion_rate":
                # Lost orders = conversion rate drop * traffic
                current_order_loss = abs_res * traffic
                current_revenue_loss = current_order_loss * avg_selling_price
                current_profit_loss = current_revenue_loss * 0.15
            elif kpi_lower == "retention_rate":
                # Retention drop impact on revenue
                current_revenue_loss = abs_res * traffic * avg_selling_price * 0.5
                current_profit_loss = current_revenue_loss * 0.15
                current_order_loss = current_revenue_loss / (avg_selling_price + 1e-5)
                
        # Recovery days estimate based on severity
        severity_lower = severity_status.lower()
        if severity_lower == "critical":
            recovery_days = 14
        elif severity_lower == "high":
            recovery_days = 7
        elif severity_lower == "medium":
            recovery_days = 4
        else:
            recovery_days = 2
            
        # Projections
        projected_revenue_loss = current_revenue_loss * recovery_days
        projected_profit_loss = current_profit_loss * recovery_days
        projected_order_loss = current_order_loss * recovery_days
        
        weekly_revenue_loss = current_revenue_loss * 7
        monthly_revenue_loss = current_revenue_loss * 30
        
        opportunity_cost = current_revenue_loss + current_profit_loss
        
        return {
            "current_revenue_loss": round(current_revenue_loss, 2),
            "current_profit_loss": round(current_profit_loss, 2),
            "current_order_loss": round(current_order_loss, 1),
            "weekly_projected_loss": round(weekly_revenue_loss, 2),
            "monthly_projected_loss": round(monthly_revenue_loss, 2),
            "projected_total_loss": round(projected_revenue_loss, 2),
            "estimated_recovery_days": recovery_days,
            "opportunity_cost": round(opportunity_cost, 2),
            "details": f"Estimated recovery window of {recovery_days} days. Total risk exposure is ${projected_revenue_loss:,.2f} in revenue."
        }
