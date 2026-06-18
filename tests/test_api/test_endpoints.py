import pytest

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_forecast_endpoint(client):
    payload = {
        "target_metric": "revenue",
        "product_id": "P001",
        "horizon_days": 10,
        "current_features": {
            "marketing_spend": 8000,
            "price": 700,
            "discount_pct": 15
        }
    }
    response = client.post("/api/v1/forecast/predict", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["target_metric"] == "revenue"
    assert data["product_id"] == "P001"
    assert data["horizon_days"] == 10
    assert len(data["forecast"]) == 10
    assert "aggregated_sum" in data
    assert "aggregated_mean" in data
    
    # Assert confidence intervals are populated and logically bounded
    first_point = data["forecast"][0]
    assert "confidence_lower" in first_point
    assert "confidence_upper" in first_point
    assert first_point["confidence_lower"] <= first_point["value"] <= first_point["confidence_upper"]

def test_predict_all_endpoint(client):
    payload = {
        "product_id": "P001",
        "horizon_days": 10,
        "current_features": {
            "marketing_spend": 8000,
            "price": 700,
            "discount_pct": 15
        }
    }
    response = client.post("/api/v1/forecast/predict_all", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["product_id"] == "P001"
    assert data["horizon_days"] == 10
    
    targets = ["revenue", "profit", "orders", "conversion_rate", "retention_rate"]
    for t in targets:
        assert t in data
        assert len(data[t]) == 10
        first_pt = data[t][0]
        assert "value" in first_pt
        assert "confidence_lower" in first_pt
        assert "confidence_upper" in first_pt
        assert first_pt["confidence_lower"] <= first_pt["value"] <= first_pt["confidence_upper"]

def test_explanation_endpoint(client):
    payload = {
        "target_metric": "revenue",
        "product_id": "P001",
        "date": "2025-01-05"
    }
    response = client.post("/api/v1/explanation/explain", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["target_metric"] == "revenue"
    assert data["product_id"] == "P001"
    assert data["date"] == "2025-01-05"
    assert "prediction_value" in data
    assert "base_value" in data
    assert "explanation_summary" in data
    assert isinstance(data["explanation_summary"], str)
    assert len(data["explanation_summary"]) > 0
    assert "positive_drivers" in data
    assert "negative_drivers" in data
    assert "global_importance" in data
    assert isinstance(data["positive_drivers"], list)
    assert isinstance(data["negative_drivers"], list)
    assert isinstance(data["global_importance"], list)
    assert len(data["global_importance"]) > 0

def test_global_importance_endpoint(client):
    response = client.get("/api/v1/explanation/global_importance?target_metric=revenue")
    assert response.status_code == 200
    
    data = response.json()
    assert data["target_metric"] == "revenue"
    assert "global_importance" in data
    assert isinstance(data["global_importance"], list)
    assert len(data["global_importance"]) > 0
    assert "feature" in data["global_importance"][0]
    assert "clean_name" in data["global_importance"][0]
    assert "importance_value" in data["global_importance"][0]

def test_scenario_endpoint(client):
    payload = {
        "target_metric": "revenue",
        "product_id": "P001",
        "horizon_days": 10,
        "modifications": {
            "discount_pct": {"type": "add", "value": 5.0}, # add 5 percentage points
            "marketing_spend": {"type": "multiply", "value": 1.20} # increase by 20%
        }
    }
    response = client.post("/api/v1/scenario/simulate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["target_metric"] == "revenue"
    assert data["product_id"] == "P001"
    assert data["horizon_days"] == 10
    assert "baseline_sum" in data
    assert "simulated_sum" in data
    assert "absolute_difference" in data
    assert "percentage_difference" in data
    assert data["impact"] in ["positive", "negative", "neutral"]
    assert len(data["daily_comparison"]) == 10

def test_optimization_endpoint(client):
    payload = {
        "target_metric": "revenue",
        "product_id": "P001",
        "horizon_days": 10,
        "max_discount_pct": 0.25,
        "max_marketing_budget": 200.0
    }
    response = client.post("/api/v1/optimization/maximize", json=payload)
    print("\nDEBUG test_optimization_endpoint:")
    print("STATUS CODE:", response.status_code)
    print("JSON:", response.json())
    assert response.status_code == 200
    
    data = response.json()
    assert data["target_metric"] == "revenue"
    assert data["product_id"] == "P001"
    assert data["horizon_days"] == 10
    assert "baseline_forecast_sum" in data
    assert "optimized_forecast_sum" in data
    assert "percentage_improvement" in data
    assert "optimal_parameters" in data
    assert "baseline_parameters" in data

def test_analysis_compare_endpoint(client):
    payload = {
        "period1_start": "2025-01-01",
        "period1_end": "2025-01-10",
        "period2_start": "2025-01-11",
        "period2_end": "2025-01-20",
        "product_id": "P001"
    }
    response = client.post("/api/v1/analysis/compare", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "period1_range" in data
    assert "period2_range" in data
    assert "metrics_comparison" in data
    assert "drivers_summary" in data

def test_analysis_declining_endpoint(client):
    payload = {
        "lookback_days": 30,
        "metric": "revenue"
    }
    response = client.post("/api/v1/analysis/declining", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "declining_products" in data
    assert isinstance(data["declining_products"], list)

def test_scenario_evaluate_endpoint(client):
    payload = {
        "product_id": "P001",
        "horizon_days": 10,
        "changes": [
            "discount +5%",
            "marketing +10%",
            "shipping +20"
        ]
    }
    response = client.post("/api/v1/scenario/evaluate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["product_id"] == "P001"
    assert data["horizon_days"] == 10
    assert data["changes"] == ["discount +5%", "marketing +10%", "shipping +20"]
    
    # Check that all 5 target KPIs are present
    targets = ["revenue", "profit", "orders", "conversion_rate", "retention_rate"]
    for t in targets:
        assert t in data["kpis"]
        kpi = data["kpis"][t]
        assert "baseline" in kpi
        assert "simulated" in kpi
        assert "absolute_difference" in kpi
        assert "percentage_difference" in kpi
        assert "impact" in kpi
        
        # Check daily comparisons
        assert t in data["daily_comparison"]
        assert len(data["daily_comparison"][t]) == 10
        first_pt = data["daily_comparison"][t][0]
        assert "date" in first_pt
        assert "baseline_value" in first_pt
        assert "simulated_value" in first_pt
        assert "difference" in first_pt

def test_scenario_evaluate_batch_endpoint(client):
    payload = {
        "product_ids": ["P001", "P002"],
        "horizon_days": 5,
        "scenarios": [
            {
                "scenario_name": "Aggressive Discounting",
                "changes": ["discount +10%", "price -5%"]
            },
            {
                "scenario_name": "Marketing Boost",
                "changes": ["marketing +20%"]
            }
        ]
    }
    response = client.post("/api/v1/scenario/evaluate_batch", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "results" in data
    results = data["results"]
    
    # We should have 2 products * 2 scenarios = 4 evaluation results
    assert len(results) == 4
    
    # Check structured content of first result
    first_res = results[0]
    assert first_res["product_id"] in ["P001", "P002"]
    assert first_res["horizon_days"] == 5
    assert first_res["scenario_name"] in ["Aggressive Discounting", "Marketing Boost"]
    assert len(first_res["changes"]) > 0
    assert "kpis" in first_res
    assert "daily_comparison" in first_res
    
    targets = ["revenue", "profit", "orders", "conversion_rate", "retention_rate"]
    for t in targets:
        assert t in first_res["kpis"]
        assert len(first_res["daily_comparison"][t]) == 5
