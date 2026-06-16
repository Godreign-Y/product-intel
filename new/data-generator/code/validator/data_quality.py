import pandas as pd
import numpy as np

class DataQualityValidator:
    """Validates Sections A, B, C, and D of the Simulation Validation spec."""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.results = {}

    def validate_all(self):
        self._check_nans()
        self._check_bounds()
        self._check_mixes()
        self._check_inventory()
        self._check_derived()
        return self.results

    def _check_nans(self):
        nan_count = int(self.df.isna().sum().sum())
        self.results["nan_count"] = nan_count

    def _check_bounds(self):
        bounds_violations = 0
        df = self.df
        
        # >= 0
        for col in ["inventory_available", "traffic", "active_users", "orders", "revenue", "discount_pct", "conversion_rate", "retention_rate", "current_ctr"]:
            if col in df.columns:
                bounds_violations += int((df[col] < 0).sum())
                
        # > 0
        for col in ["avg_selling_price", "avg_ltv"]:
            if col in df.columns:
                bounds_violations += int((df[col] <= 0).sum())
                
        # <= 100
        if "discount_pct" in df.columns:
            bounds_violations += int((df["discount_pct"] > 100).sum())
            
        # <= 1 (rates)
        for col in ["conversion_rate", "retention_rate", "current_ctr"]:
            if col in df.columns:
                bounds_violations += int((df[col] > 1.0).sum())
                
        self.results["bounds_violations"] = bounds_violations

    def _check_mixes(self):
        mix_violations = 0
        df = self.df
        
        sales_cols = [c for c in df.columns if c.startswith("sales_mix_")]
        if sales_cols:
            sales_sums = df[sales_cols].sum(axis=1)
            mix_violations += int((abs(sales_sums - 100.0) > 0.1).sum())
            
        camp_cols = [c for c in df.columns if c.startswith("campaign_mix_")]
        if camp_cols:
            camp_sums = df[camp_cols].sum(axis=1)
            mix_violations += int((abs(camp_sums - 100.0) > 0.1).sum())
            
        acq_cols = [c for c in df.columns if c.startswith("acq_mix_")]
        if acq_cols:
            acq_sums = df[acq_cols].sum(axis=1)
            mix_violations += int((abs(acq_sums - 100.0) > 0.1).sum())
            
        age_cols = [c for c in df.columns if c.startswith("age_mix_")]
        if age_cols:
            age_sums = df[age_cols].sum(axis=1)
            mix_violations += int((abs(age_sums - 100.0) > 0.1).sum())
            
        self.results["mix_violations"] = mix_violations

    def _check_inventory(self):
        df = self.df
        
        if "inventory_available" in df.columns:
            neg_inv = int((df["inventory_available"] < 0).sum())
            stockouts = int((df["inventory_available"] == 0).sum())
            
            # Count restock events (when inv jumps up)
            # Group by trajectory_id, find differences
            df_sorted = df.sort_values(by=["trajectory_id", "day"])
            inv_diff = df_sorted.groupby("trajectory_id")["inventory_available"].diff()
            
            restocks = int((inv_diff > 0).sum())
            
            self.results["negative_inventory"] = neg_inv
            self.results["stockout_events"] = stockouts
            self.results["restock_events"] = restocks

    def _check_derived(self):
        df = self.df
        derived_violations = 0
        
        if "effective_price" in df.columns and "avg_selling_price" in df.columns and "discount_pct" in df.columns:
            expected_ep = df["avg_selling_price"] * (1 - df["discount_pct"] / 100)
            derived_violations += int((abs(df["effective_price"] - expected_ep) > 0.01).sum())
            
        if "revenue" in df.columns and "fulfilled_orders" in df.columns and "effective_price" in df.columns:
            expected_rev = df["fulfilled_orders"] * df["effective_price"]
            derived_violations += int((abs(df["revenue"] - expected_rev) > 1.0).sum())
            
        self.results["derived_violations"] = derived_violations
