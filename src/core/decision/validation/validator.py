import pandas as pd
import numpy as np
import datetime
from typing import Dict, Any, List, Optional
import scipy.stats as stats

from src.core.sensitivity import SensitivityEngine
from src.core.forecaster import ProductForecaster
from src.core.simulator import ScenarioSimulator

class ValidationEngine:
    def __init__(
        self, 
        df_historical: Optional[pd.DataFrame],
        forecaster: ProductForecaster,
        sensitivity_engine: SensitivityEngine,
        simulator: ScenarioSimulator
    ):
        self.df = df_historical
        self.forecaster = forecaster
        self.sensitivity_engine = sensitivity_engine
        self.simulator = simulator

    def run_correlation(self, kpi: str, driver: str, product_id: str = "P001") -> Dict[str, Any]:
        """
        Computes Pearson and Spearman correlation coefficients.
        """
        prod_data = self.df[self.df["product_id"] == product_id].copy()
        if len(prod_data) < 10 or kpi not in prod_data.columns or driver not in prod_data.columns:
            return {"pearson": 0.0, "spearman": 0.0, "p_value": 1.0}
            
        x = prod_data[driver].astype(float).values
        y = prod_data[kpi].astype(float).values
        
        # Pearson
        try:
            p_coef, p_val = stats.pearsonr(x, y)
            import pandas as pd
            if np.isnan(p_coef) or pd.isna(p_coef): p_coef = 0.0
            if np.isnan(p_val) or pd.isna(p_val): p_val = 1.0
        except Exception:
            p_coef, p_val = 0.0, 1.0
            
        # Spearman
        try:
            s_coef, s_val = stats.spearmanr(x, y)
            import pandas as pd
            if np.isnan(s_coef) or pd.isna(s_coef): s_coef = 0.0
            if np.isnan(s_val) or pd.isna(s_val): s_val = 1.0
        except Exception:
            s_coef, s_val = 0.0, 1.0
            
        return {
            "pearson": round(float(p_coef), 4),
            "spearman": round(float(s_coef), 4),
            "p_value": round(float(p_val), 4)
        }

    def run_sensitivity_lookup(self, driver_key: str, product_id: str = "P001") -> Dict[str, Any]:
        """
        Queries the Sensitivity Engine to fetch elasticity scores and expected impact.
        """
        try:
            # Map hypothesis driver word to sensitivity keys
            driver_map = {
                "discount": "discount",
                "price": "price",
                "shipping": "shipping",
                "marketing": "marketing",
                "spend": "marketing",
                "inventory": "inventory",
                "return": "return",
                "retention": "return"
            }
            mapped_key = driver_map.get(driver_key.lower(), "discount")
            
            sensitivity_results = self.sensitivity_engine.calculate_sensitivity(
                historical_df=self.df,
                product_id=product_id
            )
            return sensitivity_results.get(mapped_key, {"elasticity_score": 0.0, "expected_impact": 0.0, "confidence": "Low"})
        except Exception as e:
            return {
                "elasticity_score": 0.0,
                "expected_impact": 0.0,
                "confidence": "Low",
                "error": str(e)
            }

    def run_forecast_simulation(self, kpi: str, driver_col: str, change_pct: float, product_id: str = "P001") -> Dict[str, Any]:
        """
        Runs counterfactual forecasting simulation on the trained models.
        """
        try:
            # Get latest values for baseline comparison
            prod_data = self.df[self.df["product_id"] == product_id].copy()
            if prod_data.empty:
                return {"baseline_forecast": 0.0, "simulated_forecast": 0.0, "delta_pct": 0.0}
                
            last_row = prod_data.iloc[-1]
            base_val = float(last_row[driver_col])
            raw_new_val = base_val * (1.0 + change_pct / 100.0) if base_val > 0 else (change_pct / 10.0)
            
            # Cast new_val to matching historical column dtype to avoid forecaster input type errors
            col_dtype = self.df[driver_col].dtype
            if np.issubdtype(col_dtype, np.integer):
                new_val = int(round(raw_new_val))
            else:
                new_val = float(raw_new_val)
            
            # Baseline forecast
            baseline = self.forecaster.forecast(
                historical_df=self.df,
                product_id=product_id,
                horizon_days=14
            )
            base_sum = float(baseline[kpi].sum()) if kpi in baseline.columns else float(baseline["revenue"].sum())
            
            # Perturbed counterfactual
            perturbed = self.forecaster.forecast(
                historical_df=self.df,
                product_id=product_id,
                horizon_days=14,
                current_features={driver_col: new_val}
            )
            sim_sum = float(perturbed[kpi].sum()) if kpi in perturbed.columns else float(perturbed["revenue"].sum())
            
            delta = sim_sum - base_sum
            pct = (delta / max(1.0, base_sum)) * 100.0
            
            return {
                "baseline_forecast": round(base_sum, 2),
                "simulated_forecast": round(sim_sum, 2),
                "expected_delta": round(delta, 2),
                "delta_pct": round(pct, 2)
            }
        except Exception as e:
            return {
                "baseline_forecast": 0.0,
                "simulated_forecast": 0.0,
                "expected_delta": 0.0,
                "delta_pct": 0.0,
                "error": str(e)
            }

    def run_causal_effect(self, kpi: str, driver: str, product_id: str = "P001") -> Dict[str, Any]:
        """
        Pluggable casual inference interface calculating average treatment effect proxy.
        """
        # Baseline ATE proxy via mean difference above median driver value (treatment control split)
        prod_data = self.df[self.df["product_id"] == product_id].copy()
        if len(prod_data) < 20 or kpi not in prod_data.columns or driver not in prod_data.columns:
            return {"ate_estimate": 0.0, "p_value": 1.0, "is_pluggable_ready": True}
            
        driver_vals = prod_data[driver].astype(float).values
        kpi_vals = prod_data[kpi].astype(float).values
        
        median_driver = np.median(driver_vals)
        treatment = kpi_vals[driver_vals > median_driver]
        control = kpi_vals[driver_vals <= median_driver]
        
        if len(treatment) < 5 or len(control) < 5:
            return {"ate_estimate": 0.0, "p_value": 1.0, "is_pluggable_ready": True}
            
        ate = np.mean(treatment) - np.mean(control)
        
        # Welch's T-test
        try:
            t_stat, p_val = stats.ttest_ind(treatment, control, equal_var=False)
            if np.isnan(p_val): p_val = 1.0
        except Exception:
            p_val = 1.0
            
        return {
            "ate_estimate": round(float(ate), 4),
            "p_value": round(float(p_val), 4),
            "is_pluggable_ready": True,
            "method": "ATE Proxy (Treatment vs Control above Median)"
        }

    def validate(self, hypothesis: Dict[str, Any], product_id: str = "P001") -> Dict[str, Any]:
        """
        Runs the full validation suite against a candidate hypothesis.
        """
        original_df = self.df
        if self.df is None:
            from src.api.dependencies import get_historical_df_from_db
            self.df = get_historical_df_from_db(product_id=product_id)
        try:
            hyp_id = hypothesis.get("hypothesis_id", "")
            affected_kpis = hypothesis.get("affected_kpis", ["total_revenue"])
            kpi = affected_kpis[0] if affected_kpis else "revenue"
            
            # Map internal Column Names
            kpi_col = "revenue" if "revenue" in kpi else "profit" if "profit" in kpi else "orders" if "orders" in kpi else "conversion_rate" if "conversion" in kpi else "revenue"
            
            # Map driver column based on hypothesis ID or keywords
            driver_col = "discount_pct"
            driver_key = "discount"
            if "shi" in hyp_id.lower() or "shipping" in hypothesis.get("title", "").lower():
                driver_col = "shipping_fee"
                driver_key = "shipping"
            elif "pri" in hyp_id.lower() or "price" in hypothesis.get("title", "").lower() or "pricing" in hypothesis.get("title", "").lower():
                driver_col = "avg_selling_price"
                driver_key = "price"
            elif "spend" in hypothesis.get("title", "").lower() or "marketing" in hypothesis.get("title", "").lower():
                driver_col = "marketing_spend"
                driver_key = "marketing"
                
            # 1. Run Correlation
            correlation = self.run_correlation(kpi_col, driver_col, product_id)
            
            # 2. Run Sensitivity
            sensitivity = self.run_sensitivity_lookup(driver_key, product_id)
            
            # 3. Run Forecast counterfactual (Simulate +10% or -10% change depending on type)
            # If it's a shipping fee cut or price drop, simulation should check negative change
            is_negative_change = "cut" in hypothesis.get("title", "").lower() or "reduce" in hypothesis.get("title", "").lower() or "drop" in hypothesis.get("title", "").lower() or "lower" in hypothesis.get("title", "").lower()
            change_pct = -10.0 if is_negative_change else 10.0
            
            forecast_sim = self.run_forecast_simulation(kpi_col, driver_col, change_pct, product_id)
            
            # 4. Run Causal Analysis
            causal = self.run_causal_effect(kpi_col, driver_col, product_id)
            
            return {
                "correlation": correlation,
                "sensitivity": sensitivity,
                "forecast_simulation": forecast_sim,
                "causal": causal,
                "validated_at": datetime.datetime.utcnow().isoformat()
            }
        finally:
            self.df = original_df
