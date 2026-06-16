from typing import List, Dict, Any

class ProductAnomalyRanker:
    def __init__(self):
        pass

    def rank_products(self, anomaly_reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Ranks and categorizes product anomalies by severity, business risk, and performance direction.
        """
        # Filter reports that actually registered anomaly calculations
        valid_reports = [r for r in anomaly_reports if "severity_score" in r]
        
        # 1. Top Critical Products
        top_critical = sorted(
            valid_reports,
            key=lambda x: x.get("severity_score", 0.0),
            reverse=True
        )
        
        # 2. Top Revenue Risk (sorted by revenue loss)
        top_revenue_risk = sorted(
            valid_reports,
            key=lambda x: x.get("business_impact", {}).get("current_revenue_loss", 0.0),
            reverse=True
        )
        # Filter out cases with zero loss
        top_revenue_risk = [r for r in top_revenue_risk if r.get("business_impact", {}).get("current_revenue_loss", 0.0) > 0.0]
        
        # 3. Top Profit Risk
        top_profit_risk = sorted(
            valid_reports,
            key=lambda x: x.get("business_impact", {}).get("current_profit_loss", 0.0),
            reverse=True
        )
        top_profit_risk = [r for r in top_profit_risk if r.get("business_impact", {}).get("current_profit_loss", 0.0) > 0.0]
        
        # 4. Most Unusual Products (sorted by multivariate score)
        most_unusual = sorted(
            valid_reports,
            key=lambda x: x.get("multivariate_details", {}).get("anomaly_score", 0.0),
            reverse=True
        )
        
        # 5. Products Recovering & Improving
        recovering = []
        improving = []
        
        for r in valid_reports:
            # Check for improvement flags
            trend_details = r.get("trend_details", {})
            flags = trend_details.get("summary_flags", [])
            
            is_improving = False
            for f in flags:
                if "slow improvement" in f.lower() or "persistent growth" in f.lower():
                    is_improving = True
                    break
                    
            residual = r.get("residual", 0.0)
            
            if is_improving or residual > 0:
                # Actual > Prediction is positive anomaly, indicating recovery/growth
                if "recovery" in str(flags).lower() or (residual > 0 and r.get("severity_score", 0.0) < 50.0):
                    recovering.append(r)
                else:
                    improving.append(r)
                    
        def format_summary(rep_list: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
            formatted = []
            for r in rep_list[:limit]:
                formatted.append({
                    "product_id": r.get("product_id"),
                    "kpi": r.get("kpi"),
                    "severity_score": r.get("severity_score"),
                    "status": r.get("status"),
                    "revenue_loss": r.get("business_impact", {}).get("current_revenue_loss", 0.0),
                    "profit_loss": r.get("business_impact", {}).get("current_profit_loss", 0.0),
                    "percent_change": r.get("percentage_change", 0.0)
                })
            return formatted
            
        return {
            "top_10_critical_products": format_summary(top_critical, 10),
            "top_revenue_risk": format_summary(top_revenue_risk, 10),
            "top_profit_risk": format_summary(top_profit_risk, 10),
            "most_unusual_products": format_summary(most_unusual, 10),
            "products_recovering": format_summary(recovering, 10),
            "products_improving": format_summary(improving, 10)
        }
