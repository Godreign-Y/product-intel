import pandas as pd
import numpy as np
from typing import List, Dict, Any
import datetime
from src.core.history.storage.models import Event

class EventDetector:
    def __init__(self, lookback_window: int = 14):
        self.lookback_window = lookback_window

    def detect_events(self, df_hist: pd.DataFrame) -> List[Event]:
        """
        Runs statistical checks across all products to detect historical anomalies.
        """
        events = []
        df = df_hist.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values(by=["product_id", "date"]).reset_index(drop=True)
        
        # Group by product to calculate rolling metrics
        for product_id, group in df.groupby("product_id"):
            group = group.sort_values(by="date").reset_index(drop=True)
            if len(group) < self.lookback_window + 5:
                continue
                
            # Calculate rolling averages and standard deviations for metrics
            rolling_cols = ["revenue", "conversion_rate", "orders", "retention_rate", "shipping_fee", "marketing_spend", "profit"]
            rolling_means = {}
            rolling_stds = {}
            
            for col in rolling_cols:
                rolling_means[col] = group[col].shift(1).rolling(window=self.lookback_window, min_periods=5).mean()
                rolling_stds[col] = group[col].shift(1).rolling(window=self.lookback_window, min_periods=5).std()
            
            # Identify outlier dates
            for i in range(self.lookback_window, len(group)):
                row = group.iloc[i]
                date_val = row["date"].date()
                
                # Check metrics
                for col in rolling_cols:
                    mean_val = rolling_means[col].iloc[i]
                    std_val = rolling_stds[col].iloc[i]
                    
                    if pd.isna(mean_val) or pd.isna(std_val) or std_val == 0:
                        continue
                        
                    val = row[col]
                    z_score = (val - mean_val) / std_val
                    
                    # 1. Spikes & Drops (Z-score thresholds)
                    if col == "revenue":
                        if z_score >= 2.2:
                            events.append(self._create_event(date_val, product_id, "Revenue Spike", "High", "revenue", 
                                          f"Revenue jumped to ${val:,.2f} (expected average: ${mean_val:,.2f}, Z-score: {z_score:.2f})", 
                                          f"Boosted total daily sales contribution, matching peak traffic metrics.", z_score))
                        elif z_score <= -2.2:
                            events.append(self._create_event(date_val, product_id, "Revenue Drop", "Critical", "revenue", 
                                          f"Revenue collapsed to ${val:,.2f} (expected average: ${mean_val:,.2f}, Z-score: {z_score:.2f})", 
                                          f"Contracted profit yields and disrupted weekly category run-rates.", abs(z_score)))
                                          
                    elif col == "conversion_rate":
                        if z_score >= 2.2:
                            events.append(self._create_event(date_val, product_id, "Conversion Increase", "Medium", "conversion_rate", 
                                          f"Conversion rate increased to {val*100:.2f}% (expected average: {mean_val*100:.2f}%)", 
                                          f"Enhanced traffic monetization effectiveness, boosting transaction counts.", z_score))
                        elif z_score <= -2.2:
                            events.append(self._create_event(date_val, product_id, "Conversion Decline", "High", "conversion_rate", 
                                          f"Conversion rate dropped to {val*100:.2f}% (expected average: {mean_val*100:.2f}%)", 
                                          f"Indicated potential checkout leakage, landing page friction, or site errors.", abs(z_score)))
                                          
                    elif col == "orders" and z_score >= 2.5:
                        events.append(self._create_event(date_val, product_id, "Demand Surge", "Medium", "orders", 
                                      f"Order volume surged to {int(val)} orders (expected average: {mean_val:.1f})", 
                                      f"Drove transactional load and increased distribution requirements.", z_score))
                                      
                    elif col == "retention_rate" and z_score >= 2.2:
                        events.append(self._create_event(date_val, product_id, "Retention Improvement", "Medium", "retention_rate", 
                                      f"Customer retention rate ticked up to {val*100:.2f}% (expected: {mean_val*100:.2f}%)", 
                                      f"Signaled increased repeat customer lifetime value and organic loyalty.", z_score))
                                      
                    elif col == "shipping_fee" and z_score >= 2.2:
                        events.append(self._create_event(date_val, product_id, "Shipping Cost Increase", "Low", "shipping_fee", 
                                      f"Average shipping fee increased to ${val:.2f} (expected: ${mean_val:.2f})", 
                                      f"Compressed net margins due to elevated third-party transit fulfillment fees.", z_score))
                                      
                    elif col == "profit" and z_score <= -2.2:
                        events.append(self._create_event(date_val, product_id, "Profit Decline", "High", "profit", 
                                      f"Profit margins compressed to ${val:,.2f} (expected average: ${mean_val:,.2f})", 
                                      f"Cannibalized daily net income distributions.", abs(z_score)))
                
                # 2. Rule-Based Checks (Inventory & Marketing)
                # Inventory Alert
                if "inventory_available" in row and row["inventory_available"] <= 5:
                    events.append(self._create_event(
                        date_val, product_id, "Inventory Risk", "Critical", "inventory",
                        f"Stock levels fell to critical levels ({int(row['inventory_available'])} units left)",
                        f"High risk of immediate stockout, halting sales for Product {product_id}.",
                        1.0
                    ))
                
                # Marketing Inefficiency (High marketing cost, low ROAS)
                if "marketing_spend" in row and "current_roas" in row:
                    m_spend = row["marketing_spend"]
                    m_mean = rolling_means["marketing_spend"].iloc[i]
                    m_std = rolling_stds["marketing_spend"].iloc[i]
                    roas = row["current_roas"]
                    
                    if not pd.isna(m_mean) and not pd.isna(m_std) and m_std > 0:
                        # Spend is high, but ROAS is poor (< 1.0 or Z-score ROAS is negative)
                        if m_spend > m_mean + 1.5 * m_std and roas < 1.0:
                            events.append(self._create_event(
                                date_val, product_id, "Marketing Inefficiency", "High", "marketing_spend, profit",
                                f"Marketing spend spiked to ${m_spend:,.2f} with an ineffective ROAS of {roas:.2f}",
                                f"Wasted marketing capital, compressing margins without driving proportional conversion boosts.",
                                1.0
                            ))
                            
        # Sort events chronologically
        events = sorted(events, key=lambda x: x.event_date)
        return events

    def _create_event(self, date_val: datetime.date, product_id: str, event_type: str, 
                      severity: str, kpis: str, reason: str, impact: str, score: float) -> Event:
        # Normalize score to confidence between 0.5 and 1.0
        confidence = min(1.0, max(0.5, 0.5 + (score / 10.0)))
        return Event(
            event_date=date_val,
            product_id=product_id,
            event_type=event_type,
            severity=severity,
            kpis_affected=kpis,
            reason=reason,
            business_impact=impact,
            confidence=round(float(confidence), 2)
        )
