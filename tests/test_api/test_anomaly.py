import pytest

def test_anomaly_detect_endpoint(client):
    payload = {
        "product_id": "P001",
        "target_date": "2025-06-15",
        "kpi": "revenue"
    }
    response = client.post("/api/v1/anomaly/detect", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["product_id"] == "P001"
    assert data["target_date"] == "2025-06-15"
    assert data["kpi"] == "REVENUE"
    assert "expected_value" in data
    assert "actual_value" in data
    assert "residual" in data
    assert "percentage_change" in data
    assert "severity_score" in data
    assert "status" in data
    assert "change_point_detected" in data
    assert "multivariate_details" in data
    assert "business_rules_triggered" in data
    assert "broken_relations" in data
    assert "business_impact" in data
    assert "historical_context" in data
    assert "explanation" in data
    assert "confidence_interval_95" in data
    assert "outside_ci" in data
    assert "trend_details" in data

def test_anomaly_product_endpoint(client):
    payload = {
        "product_id": "P001",
        "target_date": "2025-06-15",
        "kpi": "revenue"
    }
    response = client.post("/api/v1/anomaly/product", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["product_id"] == "P001"
    assert data["kpi"] == "REVENUE"

def test_anomaly_category_endpoint(client):
    payload = {
        "category": "Skincare",
        "target_date": "2025-06-15",
        "kpi": "revenue"
    }
    response = client.post("/api/v1/anomaly/category", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["category"] == "Skincare"
    assert data["target_date"] == "2025-06-15"
    assert "anomalies" in data
    assert isinstance(data["anomalies"], list)

def test_anomaly_history_endpoint(client):
    payload = {
        "product_id": "P001",
        "target_date": "2025-06-15",
        "kpi": "revenue"
    }
    response = client.post("/api/v1/anomaly/history", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["product_id"] == "P001"
    assert "historical_context" in data
    assert "forecast_monitoring" in data

def test_anomaly_root_cause_endpoint(client):
    payload = {
        "product_id": "P001",
        "target_date": "2025-06-15",
        "kpi": "revenue"
    }
    response = client.post("/api/v1/anomaly/root-cause", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["product_id"] == "P001"
    assert "root_cause" in data
    assert "triggered_rules" in data
    assert "broken_relations" in data

def test_anomaly_change_point_endpoint(client):
    payload = {
        "product_id": "P001",
        "target_date": "2025-06-15",
        "kpi": "revenue"
    }
    response = client.post("/api/v1/anomaly/change-point", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["product_id"] == "P001"
    assert "change_point_detected" in data
    assert "change_point_details" in data

def test_anomaly_business_impact_endpoint(client):
    payload = {
        "product_id": "P001",
        "target_date": "2025-06-15",
        "kpi": "revenue"
    }
    response = client.post("/api/v1/anomaly/business-impact", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["product_id"] == "P001"
    assert "business_impact" in data

from unittest.mock import patch

def test_anomaly_top_products_endpoint(client):
    mock_data = {
        "top_10_critical_products": [
            {"product_id": "P001", "kpi": "revenue", "severity_score": 85.0, "status": "critical", "revenue_loss": 5000.0, "profit_loss": 2000.0, "percent_change": -15.5}
        ],
        "top_revenue_risk": [
            {"product_id": "P001", "kpi": "revenue", "severity_score": 85.0, "status": "critical", "revenue_loss": 5000.0, "profit_loss": 2000.0, "percent_change": -15.5}
        ],
        "top_profit_risk": [
            {"product_id": "P001", "kpi": "revenue", "severity_score": 85.0, "status": "critical", "revenue_loss": 5000.0, "profit_loss": 2000.0, "percent_change": -15.5}
        ],
        "most_unusual_products": [
            {"product_id": "P001", "kpi": "revenue", "severity_score": 85.0, "status": "critical", "revenue_loss": 5000.0, "profit_loss": 2000.0, "percent_change": -15.5}
        ],
        "products_recovering": [
            {"product_id": "P001", "kpi": "revenue", "severity_score": 25.0, "status": "low", "revenue_loss": 0.0, "profit_loss": 0.0, "percent_change": 5.2}
        ],
        "products_improving": [
            {"product_id": "P001", "kpi": "revenue", "severity_score": 10.0, "status": "low", "revenue_loss": 0.0, "profit_loss": 0.0, "percent_change": 12.3}
        ]
    }
    with patch("src.core.anomaly.engine.AnomalyDetectionEngine.get_top_products", return_value=mock_data):
        payload = {
            "target_date": "2025-06-15",
            "kpi": "revenue"
        }
        response = client.post("/api/v1/anomaly/top-products", json=payload)
        print("STATUS CODE:", response.status_code)
        print("RESPONSE TEXT:", response.text)
        assert response.status_code == 200
        
        data = response.json()
        assert data["target_date"] == "2025-06-15"
        assert "top_10_critical_products" in data
        assert "top_revenue_risk" in data
        assert "top_profit_risk" in data
        assert "most_unusual_products" in data
        assert "products_recovering" in data
        assert "products_improving" in data

def test_anomaly_explain_endpoint(client):
    payload = {
        "product_id": "P001",
        "target_date": "2025-06-15",
        "kpi": "revenue"
    }
    response = client.post("/api/v1/anomaly/explain", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["product_id"] == "P001"
    assert "explanation" in data
