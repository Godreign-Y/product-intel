from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import sys
import types

import pandas as pd

sys.modules.setdefault("shap", SimpleNamespace(TreeExplainer=object))

from src.core.anomaly.engine import AnomalyDetectionEngine


def test_anomaly_rank_loads_bounded_date_window() -> None:
    df = pd.DataFrame(
        {
            "date": pd.to_datetime(["2025-12-30", "2025-12-31"]),
            "product_id": ["P001", "P002"],
            "revenue": [100.0, 200.0],
        }
    )
    forecaster = SimpleNamespace(step_residuals={})
    engine = AnomalyDetectionEngine(forecaster=forecaster, explainer=SimpleNamespace(), df_historical=None)
    fake_dependencies = types.ModuleType("src.api.dependencies")
    fake_dependencies.get_historical_df_from_db = MagicMock(return_value=df)

    with patch.dict(sys.modules, {"src.api.dependencies": fake_dependencies}):
        with patch.object(
            engine,
            "run_detection",
            side_effect=lambda product_id, target_date, kpi, skip_explanation: {
                "product_id": product_id,
                "target_date": target_date,
                "kpi": kpi,
                "severity_score": 0.1,
                "status": "Normal",
            },
        ):
            result = engine.get_top_products(date="2025-12-31", kpi="revenue")

    fake_dependencies.get_historical_df_from_db.assert_called_once_with(
        start_date="2025-09-02",
        end_date="2025-12-31",
    )
    assert result is not None
