import pandas as pd
import numpy as np
import optuna
from typing import Dict, Any, List, Optional
from src.core.forecaster import ProductForecaster
from src.utils.logger import setup_logger

logger = setup_logger("optimizer")

# Silence Optuna's per-trial logging; we log summary instead
optuna.logging.set_verbosity(optuna.logging.WARNING)


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
        max_marketing_budget: float = 250.0,
        max_shipping_fee: float = 50.0,
        n_trials: int = 40,
    ) -> Dict[str, Any]:
        """
        Uses Optuna Bayesian optimization (TPE sampler) to find the
        combination of discount, marketing spend, shipping fee, and
        inventory that maximizes the target metric over the forecast
        horizon.

        Upgrades over the previous grid search:
        - 4 controllable levers instead of 2
        - Bayesian sampling finds better optima in fewer evaluations
        - ROI-aware: penalises trials where extra marketing cost
          exceeds the projected revenue uplift
        - Returns the top-5 trial history for transparency
        - Reports impact on ALL 5 KPIs, not just the target
        """
        target_metric_cap = target_metric.lower()
        if target_metric_cap not in self.forecaster.models:
            matched = [
                t for t in self.forecaster.models.keys()
                if t.lower() == target_metric.lower()
            ]
            if matched:
                target_metric_cap = matched[0]
            else:
                raise ValueError(f"Target metric {target_metric} not supported.")

        # ── 1. Baseline Forecast ─────────────────────────────────────
        baseline_forecast = self.forecaster.forecast(
            historical_df=historical_df,
            product_id=product_id,
            horizon_days=horizon_days,
            future_overrides=None,
        )
        baseline_sum = float(np.sum(baseline_forecast[target_metric_cap].values))

        # Baseline sums for all KPIs (for the final comparison)
        all_kpis = ["revenue", "profit", "orders", "conversion_rate", "retention_rate"]
        baseline_kpi_sums = {}
        for kpi in all_kpis:
            vals = baseline_forecast[kpi].values
            if kpi in ("conversion_rate", "retention_rate"):
                baseline_kpi_sums[kpi] = float(np.mean(vals))
            else:
                baseline_kpi_sums[kpi] = float(np.sum(vals))

        # ── 2. Extract Current (Baseline) Parameters ─────────────────
        prod_data = historical_df[historical_df["product_id"] == product_id].copy()
        prod_data["date"] = pd.to_datetime(prod_data["date"])
        prod_data = prod_data.sort_values(by="date").reset_index(drop=True)
        last_history = prod_data.tail(1).iloc[0]

        baseline_discount = float(last_history["discount_pct"])
        baseline_marketing = float(last_history["marketing_spend"])
        baseline_selling_price = float(last_history["avg_selling_price"])
        baseline_shipping = float(last_history["shipping_fee"])
        baseline_inventory = float(last_history["inventory_available"])

        # Detect discount scale (0-100 vs 0-1)
        is_int_percent = baseline_discount > 1.0
        disc_divisor = 100.0 if is_int_percent else 1.0

        # Reverse-engineer base (pre-discount) price
        discount_fraction = baseline_discount / disc_divisor
        if 0.0 <= discount_fraction < 1.0:
            base_price = baseline_selling_price / (1.0 - discount_fraction)
        else:
            base_price = baseline_selling_price

        # Scale the caller-supplied discount bound into the data's scale
        max_disc_search = max_discount_pct * 100.0 if is_int_percent else max_discount_pct
        disc_upper = min(40.0 if is_int_percent else 0.40, max_disc_search)

        # Shipping upper bound (at least 2× the current value or the caller limit)
        shipping_upper = max(max_shipping_fee, baseline_shipping * 2.0)

        # Inventory bounds (±50 % of current, but at least 10)
        inv_lower = max(10.0, baseline_inventory * 0.5)
        inv_upper = baseline_inventory * 1.5

        # ── 3. Define the Optuna Objective ────────────────────────────

        def objective(trial: optuna.Trial) -> float:
            """
            Optuna maximises the negative of a minimisation target, so we
            return the metric sum directly (direction='maximize' below).
            """
            # Sample 4 controllable levers
            discount = trial.suggest_float(
                "discount_pct", 0.0, disc_upper,
            )
            marketing = trial.suggest_float(
                "marketing_spend", 5.0, max_marketing_budget,
            )
            shipping = trial.suggest_float(
                "shipping_fee", 0.0, shipping_upper,
            )
            inventory = trial.suggest_float(
                "inventory_available",
                inv_lower, inv_upper, step=1.0,
            )

            # Derive the simulated selling price from discount
            disc_frac = discount / disc_divisor
            sim_price = base_price * (1.0 - disc_frac)

            future_overrides = {
                "discount_pct": [discount] * horizon_days,
                "marketing_spend": [marketing] * horizon_days,
                "avg_selling_price": [sim_price] * horizon_days,
                "shipping_fee": [shipping] * horizon_days,
                "inventory_available": [inventory] * horizon_days,
            }

            try:
                sim_forecast = self.forecaster.forecast(
                    historical_df=historical_df,
                    product_id=product_id,
                    horizon_days=horizon_days,
                    future_overrides=future_overrides,
                )
                metric_sum = float(np.sum(sim_forecast[target_metric_cap].values))

                # ── ROI guard: penalise if extra marketing cost > revenue gain ──
                extra_marketing_cost = (marketing - baseline_marketing) * horizon_days
                sim_revenue = float(np.sum(sim_forecast["revenue"].values))
                revenue_gain = sim_revenue - baseline_kpi_sums["revenue"]

                if extra_marketing_cost > 0 and revenue_gain < extra_marketing_cost * 0.5:
                    # Heavy penalty: spending more than the revenue it generates
                    metric_sum *= 0.5

                return metric_sum

            except Exception as e:
                logger.warning(f"Optuna trial failed: {e}")
                return -1e9  # Penalise failed trials

        # ── 4. Run Bayesian Optimisation ──────────────────────────────
        sampler = optuna.samplers.TPESampler(seed=42, n_startup_trials=8)
        study = optuna.create_study(direction="maximize", sampler=sampler)

        logger.info(
            f"Running Optuna Bayesian optimisation for product {product_id} "
            f"({n_trials} trials, 4 levers, horizon={horizon_days}d)..."
        )
        study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

        best = study.best_trial
        best_discount = best.params["discount_pct"]
        best_marketing = best.params["marketing_spend"]
        best_shipping = best.params["shipping_fee"]
        best_inventory = best.params["inventory_available"]
        best_disc_frac = best_discount / disc_divisor
        best_price = base_price * (1.0 - best_disc_frac)
        best_sum = best.value

        logger.info(
            f"Optuna complete — best {target_metric}={best_sum:.2f} "
            f"(baseline={baseline_sum:.2f}, +{((best_sum - baseline_sum) / baseline_sum * 100):.1f}%)"
        )

        # ── 5. Full KPI Impact of the Winning Trial ───────────────────
        best_overrides = {
            "discount_pct": [best_discount] * horizon_days,
            "marketing_spend": [best_marketing] * horizon_days,
            "avg_selling_price": [best_price] * horizon_days,
            "shipping_fee": [best_shipping] * horizon_days,
            "inventory_available": [best_inventory] * horizon_days,
        }
        best_forecast = self.forecaster.forecast(
            historical_df=historical_df,
            product_id=product_id,
            horizon_days=horizon_days,
            future_overrides=best_overrides,
        )

        kpi_impact = {}
        for kpi in all_kpis:
            vals = best_forecast[kpi].values
            if kpi in ("conversion_rate", "retention_rate"):
                opt_val = float(np.mean(vals))
            else:
                opt_val = float(np.sum(vals))
            base_val = baseline_kpi_sums[kpi]
            diff = opt_val - base_val
            pct = (diff / base_val * 100.0) if base_val != 0 else 0.0
            kpi_impact[kpi] = {
                "baseline": round(base_val, 4),
                "optimized": round(opt_val, 4),
                "difference": round(diff, 4),
                "percentage_change": round(pct, 2),
            }

        # ── 6. Top-5 Trial History (for transparency) ─────────────────
        sorted_trials = sorted(study.trials, key=lambda t: t.value if t.value else -1e9, reverse=True)
        top_trials = []
        for t in sorted_trials[:5]:
            if t.value is None:
                continue
            t_disc = t.params["discount_pct"]
            t_price = base_price * (1.0 - t_disc / disc_divisor)
            top_trials.append({
                "trial_number": t.number,
                "metric_sum": round(t.value, 2),
                "params": {
                    "discount_pct": round(t_disc, 4),
                    "marketing_spend": round(t.params["marketing_spend"], 2),
                    "shipping_fee": round(t.params["shipping_fee"], 2),
                    "inventory_available": round(t.params["inventory_available"], 0),
                    "price": round(t_price, 2),
                },
            })

        pct_improvement = (
            (best_sum - baseline_sum) / baseline_sum * 100.0
            if baseline_sum > 0
            else 0.0
        )

        # ── 7. Return (backward-compatible + enriched) ────────────────
        return {
            "target_metric": target_metric,
            "product_id": product_id,
            "horizon_days": horizon_days,
            "optimization_method": "bayesian_tpe",
            "trials_run": n_trials,
            "baseline_forecast_sum": round(baseline_sum, 2),
            "optimized_forecast_sum": round(best_sum, 2),
            "percentage_improvement": round(pct_improvement, 2),
            "optimal_parameters": {
                "discount_pct": round(float(best_discount), 4),
                "marketing_spend": round(float(best_marketing), 2),
                "shipping_fee": round(float(best_shipping), 2),
                "inventory_available": round(float(best_inventory), 0),
                "price": round(float(best_price), 2),
            },
            "baseline_parameters": {
                "discount_pct": round(float(baseline_discount), 4),
                "marketing_spend": round(float(baseline_marketing), 2),
                "shipping_fee": round(float(baseline_shipping), 2),
                "inventory_available": round(float(baseline_inventory), 0),
                "price": round(float(baseline_selling_price), 2),
            },
            "kpi_impact": kpi_impact,
            "top_trials": top_trials,
        }
