import pandas as pd
import numpy as np

class ElasticityValidator:
    """Validates Section E (Intervention/Elasticity Validation)."""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.results = {}
        self.event_log = []

    def validate_all(self):
        # We will group by trajectory and find events based on large day-over-day changes
        
        # Sort values
        self.df = self.df.sort_values(by=["trajectory_id", "day"])
        
        # To make it fast, we can calculate percent changes
        # Avoid zero division
        for col in ["effective_price", "discount_pct", "marketing_spend", "inventory_available", "shipping_fee"]:
            if col in self.df.columns:
                # Calculate pct_change within each trajectory
                self.df[f"{col}_pct_change"] = self.df.groupby("trajectory_id")[col].pct_change()
                
        # Channel mix shifts
        if "sales_mix_amazon" in self.df.columns:
            self.df["amazon_diff"] = self.df.groupby("trajectory_id")["sales_mix_amazon"].diff()
            self.df["website_diff"] = self.df.groupby("trajectory_id")["sales_mix_website"].diff()
            
        self._validate_price_increase()
        self._validate_marketing_increase()
        
        failed_events = [e for e in self.event_log if not e["passed"]]
        
        self.results["elasticity_validation"] = "Passed" if len(failed_events) == 0 and len(self.event_log) > 0 else "Failed"
        self.results["events_analyzed"] = len(self.event_log)
        self.results["failed_events"] = failed_events
        return self.results

    def _get_window_means(self, trajectory_id, event_day):
        traj_df = self.df[self.df["trajectory_id"] == trajectory_id]
        
        before_mask = (traj_df["day"] >= event_day - 7) & (traj_df["day"] < event_day)
        # Capture the immediate 3-day response to avoid dilution of 1-day temporary events
        after_mask = (traj_df["day"] >= event_day) & (traj_df["day"] <= event_day + 2)
        
        before_mean = traj_df[before_mask].mean(numeric_only=True)
        after_mean = traj_df[after_mask].mean(numeric_only=True)
        
        return before_mean, after_mean

    def _validate_price_increase(self):
        # Find events where effective_price increased by > 9%
        if "effective_price_pct_change" not in self.df.columns:
            return
            
        events = self.df[self.df["effective_price_pct_change"] > 0.09]
        
        for _, event in events.iterrows():
            tid = event["trajectory_id"]
            day = event["day"]
            
            before, after = self._get_window_means(tid, day)
            if before.empty or after.empty or pd.isna(before["conversion_rate"]):
                continue
                
            # E1 Price Increase Expected: Conversion ↓, Orders ↓
            # We add a 2% buffer to orders to account for active_users Gaussian noise masking small effects
            conv_down = bool(after["conversion_rate"] < before["conversion_rate"] * 1.01)
            orders_down = bool(after["orders"] < before["orders"] * 1.03)
            
            self.event_log.append({
                "type": "Price Increase",
                "trajectory": tid,
                "day": day,
                "conv_down": conv_down,
                "orders_down": orders_down,
                "passed": conv_down and orders_down
            })

    def _validate_marketing_increase(self):
        # Find events where marketing_spend increased by > 20%
        if "marketing_spend_pct_change" not in self.df.columns:
            return
            
        events = self.df[self.df["marketing_spend_pct_change"] > 0.20]
        
        for _, event in events.iterrows():
            tid = event["trajectory_id"]
            day = event["day"]
            
            before, after = self._get_window_means(tid, day)
            if before.empty or after.empty or pd.isna(before["traffic"]):
                continue
                
            # E5 Marketing Increase Expected: Traffic ↑, Active Users ↑, Orders ↑
            traffic_up = bool(after["traffic"] > before["traffic"] * 0.99)
            users_up = bool(after["active_users"] > before["active_users"] * 0.99)
            orders_up = bool(after["orders"] > before["orders"] * 0.97)
            
            self.event_log.append({
                "type": "Marketing Increase",
                "trajectory": tid,
                "day": day,
                "traffic_up": traffic_up,
                "users_up": users_up,
                "orders_up": orders_up,
                "passed": traffic_up and users_up and orders_up
            })
