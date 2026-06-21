import math
from scipy import stats
from typing import Dict, Any, List, Optional

from src.core.decision.config_loader import load_decision_config

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

    def _compute_sample_size(self, baseline_rate: float, mde_pct: float) -> int:
        """
        Proper two-proportion z-test sample size calculation using scipy.stats.
        Returns required sample size per variant.
        """
        z_alpha = stats.norm.ppf(1 - self.alpha / 2)  # ~1.96 for α=0.05
        z_beta = stats.norm.ppf(self.power)             # ~0.84 for power=0.80

        p1 = baseline_rate
        p2 = p1 * (1 + mde_pct / 100.0)

        # Prevent degenerate cases
        if abs(p1 - p2) < 1e-8:
            return 2000  # fallback

        pooled = (p1 + p2) / 2.0
        numerator = (
            z_alpha * math.sqrt(2 * pooled * (1 - pooled)) +
            z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
        ) ** 2
        denominator = (p1 - p2) ** 2

        n = int(math.ceil(numerator / denominator))
        return max(500, n)  # floor at 500 per variant

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
        # Extract baseline conversion from context if available
        baseline_conversion = 0.035  # default ~3.5%
        daily_traffic = self.default_daily_traffic

        if context:
            kpis = context.get("kpis", {})
            # Use actual conversion rate if available
            conv_rate = kpis.get("mean_conversion_rate", 0.0)
            if conv_rate > 0:
                baseline_conversion = float(conv_rate)
            # Use actual daily traffic: total_orders / 30 as proxy
            total_orders = kpis.get("total_orders", 0)
            if total_orders > 0:
                daily_traffic = max(10, int(total_orders / 30))

        # MDE from config (or could be derived from data variance in future)
        mde_pct = self.default_mde_pct

        # Proper power analysis via two-proportion z-test
        variant_sample_size = self._compute_sample_size(baseline_conversion, mde_pct)
        total_sample_size = variant_sample_size * 2

        # Calculate duration based on actual product traffic
        duration_days = math.ceil(total_sample_size / max(1, daily_traffic))
        duration_days = max(self.min_duration, min(self.max_duration, duration_days))
        
        # Format the metric name for readability
        metric_label = primary_metric.replace("mean_", "").replace("total_", "").replace("_", " ").title()
        
        return {
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
