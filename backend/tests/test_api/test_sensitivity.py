import pytest

def test_sensitivity_estimate(client):
    payload = {
        "product_id": "P001",
        "horizon_days": 10
    }
    response = client.post("/api/v1/sensitivity/estimate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    drivers = ["marketing", "discount", "shipping", "price", "inventory", "return"]
    for d in drivers:
        assert d in data
        item = data[d]
        assert "elasticity_score" in item
        assert "expected_impact" in item
        assert "confidence" in item
        assert isinstance(item["elasticity_score"], float)
        assert isinstance(item["expected_impact"], float)
        assert item["confidence"] in ["High", "Medium", "Low"]
