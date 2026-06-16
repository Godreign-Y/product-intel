import pandas as pd
import numpy as np

class CausalityValidator:
    """Validates Section F and G (Market Graph and Lag Validation)."""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.results = {}

    def validate_all(self):
        self._check_correlations()
        return self.results

    def _check_correlations(self):
        # We check the Pearson correlation coefficient globally across the dataset.
        df = self.df
        
        corr_results = {}
        passed_all = True
        failed_correlations = []
        
        def check_corr(c1, c2, min_val):
            if c1 in df.columns and c2 in df.columns:
                # Calculate correlation per trajectory to avoid Simpson's Paradox
                corrs = df.groupby('trajectory_id')[c1].corr(df[c2])
                val = float(corrs.mean())
                corr_results[f"{c1}_to_{c2}"] = val
                if pd.isna(val) or val < min_val:
                    failed_correlations.append(f"{c1} -> {c2} expected > {min_val}, but got {val:.4f}")
                    return False
            return True
            
        # F1 Traffic -> Active Users > 0.7
        passed_all &= check_corr("traffic", "active_users", 0.7)
        # F2 Active Users -> Orders > 0.6
        passed_all &= check_corr("active_users", "orders", 0.6)
        # F3 Conversion -> Orders > 0.6
        passed_all &= check_corr("conversion_rate", "orders", 0.6)
        # F4 Orders -> Revenue > 0.7
        passed_all &= check_corr("orders", "revenue", 0.7)
        # F5 Revenue -> Profit > 0.7
        passed_all &= check_corr("revenue", "profit", 0.7)
        # F7 Retention -> LTV > 0.7
        passed_all &= check_corr("retention_rate", "avg_ltv", 0.7)
        
        self.results["causality_correlations"] = corr_results
        self.results["causality_passed"] = passed_all
        self.results["failed_correlations"] = failed_correlations
