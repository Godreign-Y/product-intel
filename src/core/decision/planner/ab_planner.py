import math
from typing import Dict, Any, List

class ExperimentPlanner:
    def __init__(self):
        pass

    def plan_experiment(self, recommendation: Dict[str, Any], primary_metric: str) -> Dict[str, Any]:
        """
        Formulates an A/B test plan including suggested duration, sample size, and metric boundaries.
        """
        # Minimum detectable effect (MDE) defaults to 5% (0.05) or can be derived
        mde_pct = 5.0
        
        # Power analysis sample size approximation:
        # N = 16 * (sigma^2) / (MDE^2)
        # Using a conservative standard heuristic for e-commerce conversion rates:
        # N = 3200 / (MDE_pct^2) per variant (assuming baseline conversion of ~3-5%)
        variant_sample_size = int(3200 / ((mde_pct / 100.0) * 100.0) ** 2)
        variant_sample_size = max(1000, variant_sample_size)  # floor sample size
        total_sample_size = variant_sample_size * 2
        
        # Calculate suggested duration based on sample size and typical daily traffic
        # Default daily orders / visitors proxy: e.g., 200 daily visitors/orders per product
        daily_traffic_proxy = 150
        duration_days = math.ceil(total_sample_size / daily_traffic_proxy)
        duration_days = max(14, min(60, duration_days))  # bound between 2 and 8 weeks
        
        # Format the metric name for readability
        metric_label = primary_metric.replace("mean_", "").replace("total_", "").replace("_", " ").title()
        
        return {
            "experiment_type": "Two-Sample Independent A/B Test",
            "suggested_duration_days": duration_days,
            "required_sample_size": total_sample_size,
            "primary_metric": primary_metric,
            "min_detectable_effect": f"{mde_pct}%",
            "success_criteria": {
                "metric": primary_metric,
                "target_delta": f"+{mde_pct}%",
                "statistical_significance": "p-value < 0.05 (Welch's T-Test)",
                "power": "0.80 (80%)"
            },
            "rollback_trigger": f"Revert if primary metric {metric_label} drops by more than 3% in treatment group."
        }
