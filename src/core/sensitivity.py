import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

from src.core.forecaster import ProductForecaster
from src.utils.logger import setup_logger

logger = setup_logger("sensitivity")

class SensitivityEngine:
    def __init__(self, forecaster: ProductForecaster):
        self.forecaster = forecaster

    def calculate_sensitivity(
        self,
        historical_df: pd.DataFrame,
        product_id: str,
        horizon_days: int = 30
    ) -> Dict[str, Any]:
        """
        Estimates the sensitivity (elasticity, expected absolute impact, and statistical confidence)
        of cumulative predicted Revenue to changes in: Marketing, Discount, Shipping, Price, Inventory, and Retention (Return).
        """
        # 1. Filter and extract baseline variables for the product
        prod_data = historical_df[historical_df["product_id"] == product_id].copy()
        if len(prod_data) == 0:
            matched_prod = [p for p in historical_df["product_id"].unique() if str(p).lower() == str(product_id).lower()]
            if matched_prod:
                prod_data = historical_df[historical_df["product_id"] == matched_prod[0]].copy()
            else:
                raise ValueError(f"Product ID {product_id} not found in historical data.")
                
        prod_data["date"] = pd.to_datetime(prod_data["date"])
        prod_data = prod_data.sort_values(by="date")
        
        last_row = prod_data.iloc[-1]
        
        base_marketing = float(last_row["marketing_spend"])
        base_discount = float(last_row["discount_pct"])
        base_shipping = float(last_row["shipping_fee"])
        base_price = float(last_row["avg_selling_price"])
        base_inventory = float(last_row["inventory_available"])
        base_retention = float(last_row["retention_rate"])
        
        # 2. Run Baseline Forecast
        baseline_forecast = self.forecaster.forecast(
            historical_df=historical_df,
            product_id=product_id,
            horizon_days=horizon_days
        )
        base_revenue_sum = float(baseline_forecast["revenue"].sum())
        
        # 3. Calculate cumulative standard error of the revenue forecast
        step_stds = self.forecaster.step_residuals.get("revenue", [])
        if step_stds:
            # Cumulative variance sum of step errors
            var_sum = sum(step_stds[i]**2 if i < len(step_stds) else step_stds[-1]**2 for i in range(horizon_days))
            se_revenue = np.sqrt(var_sum)
        else:
            se_revenue = 0.0
            
        # Fallback if standard error is zero
        if se_revenue <= 0.0:
            se_revenue = base_revenue_sum * 0.05 + 1.0  # 5% of base revenue as proxy std error
            
        def cast_to_dtype(col_name: str, value: float) -> Any:
            col_dtype = historical_df[col_name].dtype
            if np.issubdtype(col_dtype, np.integer):
                return int(round(value))
            return float(value)

        # 4. Set up perturbations
        # We perturb each variable by +10% relative to its baseline value.
        # If baseline is 0, we perturb by adding a default unit value.
        perturbations = {
            "marketing": {
                "features": {"marketing_spend": cast_to_dtype("marketing_spend", base_marketing * 1.10 if base_marketing > 0 else 100.0)},
                "label": "Marketing Spend"
            },
            "discount": {
                "features": {"discount_pct": cast_to_dtype("discount_pct", base_discount * 1.10 if base_discount > 0 else 5.0)},
                "label": "Discount Percentage"
            },
            "shipping": {
                "features": {"shipping_fee": cast_to_dtype("shipping_fee", base_shipping * 1.10 if base_shipping > 0 else 10.0)},
                "label": "Shipping Fee"
            },
            "price": {
                "features": {"avg_selling_price": cast_to_dtype("avg_selling_price", base_price * 1.10 if base_price > 0 else 50.0)},
                "label": "Average Selling Price"
            },
            "inventory": {
                "features": {"inventory_available": cast_to_dtype("inventory_available", base_inventory * 1.10 if base_inventory > 0 else 100.0)},
                "label": "Inventory Available"
            },
            "return": { # Represented by retention_rate in the models
                "features": {"retention_rate": cast_to_dtype("retention_rate", min(1.0, base_retention * 1.10 if base_retention > 0 else 0.50))},
                "label": "Retention Rate"
            }
        }
        
        results = {}
        for key, p_info in perturbations.items():
            features_override = p_info["features"]
            
            # Predict perturbed forecast
            perturbed_forecast = self.forecaster.forecast(
                historical_df=historical_df,
                product_id=product_id,
                horizon_days=horizon_days,
                current_features=features_override
            )
            perturbed_revenue_sum = float(perturbed_forecast["revenue"].sum())
            
            # Calculate elasticity and absolute impact
            expected_impact = perturbed_revenue_sum - base_revenue_sum
            pct_change_revenue = (expected_impact / (base_revenue_sum + 1e-5)) * 100.0
            
            # Elasticity score: % change in revenue per 10% change in driver
            elasticity_score = pct_change_revenue / 10.0
            
            # Determine confidence rating based on se_revenue
            abs_impact = abs(expected_impact)
            if abs_impact > 1.96 * se_revenue:
                confidence = "High"
            elif abs_impact > 1.0 * se_revenue:
                confidence = "Medium"
            else:
                confidence = "Low"
                
            results[key] = {
                "elasticity_score": round(elasticity_score, 4),
                "expected_impact": round(expected_impact, 2),
                "confidence": confidence
            }
            
        return results
