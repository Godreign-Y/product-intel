import math
from scipy import stats
from typing import Dict, Any, List, Optional

from src.core.decision.config_loader import load_decision_config
from src.utils.logger import setup_logger

logger = setup_logger("experiment_planner")

class ExperimentPlanner:
    def __init__(self):
        cfg = load_decision_config()
        ab_cfg = cfg.get("ab_test", {})
        self.default_mde_pct = ab_cfg.get("mde_pct", 5.0)
        self.default_daily_traffic = ab_cfg.get("default_daily_traffic", 150)
        self.min_duration = ab_cfg.get("min_duration_days", 14)
        self.max_duration = ab_cfg.get("max_duration_days", 60)
        self.alpha = ab_cfg.get("alpha", 0.05)
        self.power = ab_cfg.get("power", 0.80)
        logger.info(f"Initialized ExperimentPlanner: alpha={self.alpha}, power={self.power}, duration_bounds=[{self.min_duration}, {self.max_duration}]")

    def _compute_sample_size(self, baseline_rate: float, mde_pct: float) -> int:
        """
        Proper two-proportion z-test sample size calculation using scipy.stats.
        Returns required sample size per variant.
        """
        logger.info(f"_compute_sample_size: Initiating power calculation. baseline_rate={baseline_rate:.4f}, mde_pct={mde_pct}%")
        z_alpha = stats.norm.ppf(1 - self.alpha / 2)  # ~1.96 for α=0.05
        z_beta = stats.norm.ppf(self.power)             # ~0.84 for power=0.80
        logger.debug(f"_compute_sample_size: Critical values - z_alpha={z_alpha:.4f}, z_beta={z_beta:.4f}")

        p1 = baseline_rate
        p2 = p1 * (1 + mde_pct / 100.0)

        # Prevent degenerate cases
        if abs(p1 - p2) < 1e-8:
            logger.warning("_compute_sample_size: Target proportions are identical. Returning fallback size=2000 per variant.")
            return 2000  # fallback

        pooled = (p1 + p2) / 2.0
        numerator = (
            z_alpha * math.sqrt(2 * pooled * (1 - pooled)) +
            z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
        ) ** 2
        denominator = (p1 - p2) ** 2

        n = int(math.ceil(numerator / denominator))
        result = max(500, n)  # floor at 500 per variant
        logger.info(f"_compute_sample_size: Calculated sample size={n} per variant (Floor applied: {result})")
        return result

    def plan_experiment(
        self, 
        recommendation: Dict[str, Any], 
        primary_metric: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Formulates an A/B test plan with proper power analysis.
        Uses live traffic data from context when available.
        """
        logger.info(f"plan_experiment: Designing experimental A/B plan for recommendation primary_metric='{primary_metric}'")
        
        # Extract baseline conversion from context if available
        baseline_conversion = 0.035  # default ~3.5%
        daily_traffic = self.default_daily_traffic

        if context:
            kpis = context.get("kpis", {})
            # Use actual conversion rate if available
            conv_rate = kpis.get("mean_conversion_rate", 0.0)
            if conv_rate > 0:
                baseline_conversion = float(conv_rate)
                logger.debug(f"plan_experiment: Extracted live conversion baseline from context={baseline_conversion:.4f}")
            # Use actual daily traffic: total_orders / 30 as proxy
            total_orders = kpis.get("total_orders", 0)
            if total_orders > 0:
                daily_traffic = max(10, int(total_orders / 30))
                logger.debug(f"plan_experiment: Extracted live daily traffic proxy from context={daily_traffic} daily orders")

        # MDE from config (or could be derived from data variance in future)
        mde_pct = self.default_mde_pct

        # Proper power analysis via two-proportion z-test
        variant_sample_size = self._compute_sample_size(baseline_conversion, mde_pct)
        total_sample_size = variant_sample_size * 2

        # Calculate duration based on actual product traffic
        duration_days = math.ceil(total_sample_size / max(1, daily_traffic))
        duration_days = max(self.min_duration, min(self.max_duration, duration_days))
        logger.info(f"plan_experiment: Required sample size={total_sample_size}. Estimated daily traffic={daily_traffic}. Calculated duration={duration_days} days.")
        
        # Format the metric name for readability
        metric_label = primary_metric.replace("mean_", "").replace("total_", "").replace("_", " ").title()
        
        plan = {
            "experiment_type": "Two-Sample Independent A/B Test",
            "suggested_duration_days": duration_days,
            "required_sample_size": total_sample_size,
            "sample_per_variant": variant_sample_size,
            "primary_metric": primary_metric,
            "min_detectable_effect": f"{mde_pct}%",
            "baseline_rate": round(baseline_conversion, 4),
            "estimated_daily_traffic": daily_traffic,
            "success_criteria": {
                "metric": primary_metric,
                "target_delta": f"+{mde_pct}%",
                "statistical_significance": f"p-value < {self.alpha} (Welch's T-Test)",
                "power": f"{self.power:.2f} ({int(self.power * 100)}%)"
            },
            "rollback_trigger": f"Revert if primary metric {metric_label} drops by more than 3% in treatment group."
        }
        logger.info(f"plan_experiment: A/B plan successfully generated: {plan['experiment_type']}, duration={plan['suggested_duration_days']} days.")
        return plan
