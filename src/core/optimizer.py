import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from src.core.forecaster import ProductForecaster
from src.utils.logger import setup_logger

logger = setup_logger("optimizer")

class RevenueOptimizer:
    def __init__(self, forecaster: ProductForecaster):
        self.forecaster = forecaster

    def optimize_parameters(
        self,
        historical_df: pd.DataFrame,
        product_id: str,
        horizon_days: int,
        target_metric: str,
        max_discount_pct: float = 0.30,
        max_marketing_budget: float = 250.0
    ) -> Dict[str, Any]:
        """
        Finds the combination of discount_pct and marketing_spend that maximizes the sum of
        the target metric (revenue or profit) over the forecast horizon.
        """
        target_metric_cap = target_metric.lower()
        if target_metric_cap not in self.forecaster.models:
            matched = [t for t in self.forecaster.models.keys() if t.lower() == target_metric.lower()]
            if matched:
                target_metric_cap = matched[0]
            else:
                raise ValueError(f"Target metric {target_metric} not supported.")

        # 1. Calculate Baseline Forecast Sum
        baseline_forecast = self.forecaster.forecast(
            historical_df=historical_df,
            product_id=product_id,
            horizon_days=horizon_days,
            future_overrides=None
        )
        baseline_sum = float(np.sum(baseline_forecast[target_metric_cap].values))
        
        # 2. Get baseline values for comparison
        prod_data = historical_df[historical_df["product_id"] == product_id].copy()
        prod_data["date"] = pd.to_datetime(prod_data["date"])
        prod_data = prod_data.sort_values(by="date").reset_index(drop=True)
        last_history = prod_data.tail(1).iloc[0]
        
        baseline_discount = last_history["discount_pct"]
        baseline_marketing = last_history["marketing_spend"]
        baseline_selling_price = last_history["avg_selling_price"]
        
        # Determine discount scale (0-100 vs 0-1)
        is_int_percent = baseline_discount > 1.0
        
        # Reverse-engineer base price before discount
        disc_divisor = 100.0 if is_int_percent else 1.0
        discount_fraction = baseline_discount / disc_divisor
        
        if discount_fraction >= 1.0 or discount_fraction < 0.0:
            # Fallback if baseline discount is invalid
            base_price = baseline_selling_price
        else:
            base_price = baseline_selling_price / (1.0 - discount_fraction)
        
        # 3. Define the Search Grid
        # Scale discount bound
        max_disc_search = max_discount_pct * 100.0 if is_int_percent else max_discount_pct
        
        discount_grid = np.linspace(0.0, min(40.0 if is_int_percent else 0.40, max_disc_search), 6)
        marketing_grid = np.linspace(5.0, max_marketing_budget, 6)
        
        best_sum = -np.inf
        best_discount = baseline_discount
        best_marketing = baseline_marketing
        best_price = baseline_selling_price
        
        logger.info(f"Running grid search optimization for product {product_id} over {len(discount_grid) * len(marketing_grid)} iterations...")
        
        for discount in discount_grid:
            for marketing in marketing_grid:
                # Calculate corresponding simulated avg_selling_price
                disc_frac = discount / disc_divisor
                sim_price = base_price * (1.0 - disc_frac)
                
                # Setup future overrides
                future_overrides = {
                    "discount_pct": [discount] * horizon_days,
                    "marketing_spend": [marketing] * horizon_days,
                    "avg_selling_price": [sim_price] * horizon_days
                }
                
                try:
                    sim_forecast = self.forecaster.forecast(
                        historical_df=historical_df,
                        product_id=product_id,
                        horizon_days=horizon_days,
                        future_overrides=future_overrides
                    )
                    
                    sim_sum = float(np.sum(sim_forecast[target_metric_cap].values))
                    
                    if sim_sum > best_sum:
                        best_sum = sim_sum
                        best_discount = discount
                        best_marketing = marketing
                        best_price = sim_price
                except Exception as e:
                    logger.error(f"Error forecasting during optimization for discount={discount}, marketing={marketing}: {e}")
                    
        pct_improvement = ((best_sum - baseline_sum) / baseline_sum * 100.0) if baseline_sum > 0 else 0.0
        
        # Return optimized comparison report
        return {
            "target_metric": target_metric,
            "product_id": product_id,
            "horizon_days": horizon_days,
            "baseline_forecast_sum": round(baseline_sum, 2),
            "optimized_forecast_sum": round(best_sum, 2),
            "percentage_improvement": round(pct_improvement, 2),
            "optimal_parameters": {
                "discount_pct": round(float(best_discount), 4),
                "marketing_spend": round(float(best_marketing), 2),
                "price": round(float(best_price), 2)
            },
            "baseline_parameters": {
                "discount_pct": round(float(baseline_discount), 4),
                "marketing_spend": round(float(baseline_marketing), 2),
                "price": round(float(baseline_selling_price), 2)
            }
        }
