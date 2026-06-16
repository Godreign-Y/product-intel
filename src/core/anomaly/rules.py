import os
import yaml
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

class BusinessRuleEngine:
    def __init__(self, rules_path: str = "config/anomaly_rules.yaml"):
        self.rules_path = rules_path
        self.rules = self.load_rules()

    def load_rules(self) -> List[Dict[str, Any]]:
        """
        Loads rules from YAML config or falls back to hardcoded defaults if not found.
        """
        if os.path.exists(self.rules_path):
            try:
                with open(self.rules_path, "r") as f:
                    data = yaml.safe_load(f)
                    return data.get("rules", [])
            except Exception as e:
                # Log or handle
                pass
                
        # Hardcoded fallback rules
        return [
            {
                "id": "RULE_001",
                "name": "INVENTORY_ZERO_ORDERS_POSITIVE",
                "description": "Orders or revenue occurred while available inventory was zero.",
                "severity": "CRITICAL",
                "confidence": 1.0,
                "business_explanation": "Systems indicate sales of an out-of-stock item, suggesting database mismatch.",
                "recommended_action": "Audit physical inventory and check sync script."
            },
            {
                "id": "RULE_002",
                "name": "INVENTORY_NEGATIVE",
                "description": "Available inventory fell below zero.",
                "severity": "HIGH",
                "confidence": 1.0,
                "business_explanation": "Inventory is reported as negative.",
                "recommended_action": "Sync stock levels with the ERP inventory database."
            }
        ]

    def evaluate_rules(
        self,
        df: pd.DataFrame,
        product_id: str,
        target_date: str
    ) -> List[Dict[str, Any]]:
        """
        Evaluates the business rules for a given product and date.
        """
        prod_df = df[df["product_id"] == product_id].copy()
        prod_df["date"] = pd.to_datetime(prod_df["date"])
        prod_df = prod_df.sort_values(by="date").reset_index(drop=True)
        
        target_ts = pd.to_datetime(target_date)
        target_idx_list = prod_df[prod_df["date"] == target_ts].index.tolist()
        
        if not target_idx_list:
            return []
            
        idx = target_idx_list[0]
        
        # Get target row values
        row = prod_df.iloc[idx]
        
        inventory = float(row.get("inventory_available", 0))
        orders = float(row.get("orders", 0))
        revenue = float(row.get("revenue", 0))
        profit = float(row.get("profit", 0))
        ctr = float(row.get("current_ctr", 0))
        conversion = float(row.get("conversion_rate", 0))
        discount = float(row.get("discount_pct", 0))
        shipping = float(row.get("shipping_fee", 0))
        marketing = float(row.get("marketing_spend", 0))
        traffic = float(row.get("traffic", 0))
        
        # Get previous row/history values for comparison
        prev_row = prod_df.iloc[idx - 1] if idx > 0 else row
        prev_marketing = float(prev_row.get("marketing_spend", 0))
        prev_revenue = float(prev_row.get("revenue", 0))
        prev_discount = float(prev_row.get("discount_pct", 0))
        prev_orders = float(prev_row.get("orders", 0))
        prev_shipping = float(prev_row.get("shipping_fee", 0))
        prev_conversion = float(prev_row.get("conversion_rate", 0))
        
        # Historical baseline logic (7-day window before target)
        hist_slice = prod_df.iloc[max(0, idx - 7):idx]
        avg_traffic = float(hist_slice["traffic"].mean()) if len(hist_slice) > 0 else traffic
        avg_orders = float(hist_slice["orders"].mean()) if len(hist_slice) > 0 else orders
        
        triggered_rules = []
        
        for rule in self.rules:
            rule_id = rule["id"]
            triggered = False
            
            # Rule 1: Inventory zero, orders positive
            if rule_id == "RULE_001" or rule.get("name") == "INVENTORY_ZERO_ORDERS_POSITIVE":
                if inventory == 0 and (orders > 0 or revenue > 0):
                    triggered = True
                    
            # Rule 2: Inventory negative
            elif rule_id == "RULE_002" or rule.get("name") == "INVENTORY_NEGATIVE":
                if inventory < 0:
                    triggered = True
                    
            # Rule 3: Marketing doubled, revenue unchanged
            elif rule_id == "RULE_003" or rule.get("name") == "MARKETING_DOUBLED_REVENUE_UNCHANGED":
                if prev_marketing > 0 and (marketing >= 2.0 * prev_marketing):
                    rev_change_pct = abs(revenue - prev_revenue) / (prev_revenue + 1e-5)
                    if rev_change_pct <= 0.05: # Less than 5% change in revenue
                        triggered = True
                        
            # Rule 4: Discount increased, orders decreased
            elif rule_id == "RULE_004" or rule.get("name") == "DISCOUNT_INCREASED_ORDERS_DECREASED":
                # discount is stored as percentage (0-100 or 0-1)
                disc_diff = discount - prev_discount
                # check scale of discount (let's check if it increased by more than 2% or 0.02)
                is_pct_scale = prev_discount > 1.0 or discount > 1.0
                thresh = 2.0 if is_pct_scale else 0.02
                if disc_diff > thresh and orders < prev_orders * 0.95: # orders fell by >5%
                    triggered = True
                    
            # Rule 5: CTR high, conversion collapsed
            elif rule_id == "RULE_005" or rule.get("name") == "CTR_HIGH_CONVERSION_COLLAPSED":
                if ctr > 0.04 and conversion < 0.01:
                    triggered = True
                    
            # Rule 6: Traffic normal, orders collapsed
            elif rule_id == "RULE_006" or rule.get("name") == "TRAFFIC_NORMAL_ORDERS_COLLAPSED":
                # Traffic is normal (within 30% of average)
                is_traffic_normal = (traffic >= 0.7 * avg_traffic) and (traffic <= 1.3 * avg_traffic)
                # Orders collapsed (less than 20% of normal average orders)
                if is_traffic_normal and orders < 0.2 * avg_orders and avg_orders > 2.0:
                    triggered = True
                    
            # Rule 7: Profit negative, revenue increasing
            elif rule_id == "RULE_007" or rule.get("name") == "PROFIT_NEGATIVE_REVENUE_INCREASING":
                if profit < 0 and revenue > prev_revenue * 1.02: # revenue increased by >2%
                    triggered = True
                    
            # Rule 8: Shipping increased, conversion decreased
            elif rule_id == "RULE_008" or rule.get("name") == "SHIPPING_INCREASED_CONVERSION_DECREASED":
                if prev_shipping > 0 and (shipping >= 1.3 * prev_shipping): # shipping increased by >30%
                    if conversion < prev_conversion * 0.90: # conversion fell by >10%
                        triggered = True
                        
            if triggered:
                triggered_rules.append({
                    "rule_id": rule["id"],
                    "rule_name": rule.get("name", rule["id"]),
                    "description": rule["description"],
                    "severity": rule["severity"],
                    "confidence": rule.get("confidence", 0.9),
                    "business_explanation": rule["business_explanation"],
                    "recommended_action": rule["recommended_action"]
                })
                
        return triggered_rules
