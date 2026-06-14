import pytest

def test_analytics_kpi(client):
    payload = {
        "start_date": "2025-01-01",
        "end_date": "2025-01-10",
        "product_id": "P001"
    }
    response = client.post("/api/v1/analytics/kpi", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "revenue" in data
    assert "sum" in data["revenue"]
    assert "daily_avg" in data["revenue"]
    assert "profit" in data
    assert "profit_margin" in data["profit"]
    assert "orders" in data
    assert "traffic" in data
    assert "conversion_rate" in data
    assert "mean" in data["conversion_rate"]
    assert "retention_rate" in data
    assert "marketing_spend" in data
    assert "days_in_period" in data
    assert data["days_in_period"] == 10

def test_analytics_trend(client):
    payload = {
        "metric": "revenue",
        "start_date": "2025-01-01",
        "end_date": "2025-01-10",
        "product_id": "P001"
    }
    response = client.post("/api/v1/analytics/trend", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["metric"] == "revenue"
    assert "direction" in data
    assert data["direction"] in ["increasing", "decreasing", "stable"]
    assert "slope" in data
    assert "r_squared" in data
    assert "p_value" in data
    assert "growth_rate_pct" in data
    assert "history" in data
    assert isinstance(data["history"], list)

def test_analytics_benchmark(client):
    payload = {
        "product_id": "P001",
        "start_date": "2025-01-01",
        "end_date": "2025-01-10"
    }
    response = client.post("/api/v1/analytics/benchmark", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["product_id"] == "P001"
    assert "category" in data
    assert "comparisons" in data
    comparisons = data["comparisons"]
    for key in ["asp", "cvr", "retention", "profit_margin", "marketing_efficiency"]:
        assert key in comparisons
        detail = comparisons[key]
        assert "product_value" in detail
        assert "category_benchmark" in detail
        assert "global_benchmark" in detail
        assert "pct_vs_category" in detail
        assert "pct_vs_global" in detail

def test_analytics_seasonality(client):
    payload = {
        "start_date": "2025-01-01",
        "end_date": "2025-01-10",
        "product_id": "P001"
    }
    response = client.post("/api/v1/analytics/seasonality", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "day_of_week_avg" in data
    assert "weekend_vs_weekday" in data
    assert "monthly_avg" in data
    
    # Check weekend vs weekday detail
    w_detail = data["weekend_vs_weekday"]
    assert "weekday" in w_detail
    assert "weekend" in w_detail
    assert "revenue_lift_pct" in w_detail
    assert "orders_lift_pct" in w_detail

def test_analytics_channel(client):
    payload = {
        "start_date": "2025-01-01",
        "end_date": "2025-01-10",
        "product_id": "P001"
    }
    response = client.post("/api/v1/analytics/channel", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "channel_mix" in data
    assert "estimated_revenue" in data
    assert "estimated_orders" in data
    assert "top_channel" in data
    assert "channel" in data["top_channel"]
    assert "share" in data["top_channel"]
    for c in ["Amazon", "Website", "Nykaa", "MobileApp"]:
        assert c in data["channel_mix"]
        assert c in data["estimated_revenue"]
        assert c in data["estimated_orders"]

def test_analytics_campaign(client):
    payload = {
        "start_date": "2025-01-01",
        "end_date": "2025-01-10",
        "product_id": "P001"
    }
    response = client.post("/api/v1/analytics/campaign", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "campaign_mix" in data
    assert "estimated_spend" in data
    assert "top_campaign_type" in data
    assert "campaign" in data["top_campaign_type"]
    assert "share" in data["top_campaign_type"]
    assert "general_metrics" in data
    assert "avg_ctr" in data["general_metrics"]
    assert "avg_roas" in data["general_metrics"]
    for c in ["Search", "Social", "Email", "Affiliate"]:
        assert c in data["campaign_mix"]
        assert c in data["estimated_spend"]

def test_analytics_inventory(client):
    payload = {
        "product_id": "P001",
        "start_date": "2025-01-01",
        "end_date": "2025-01-10"
    }
    response = client.post("/api/v1/analytics/inventory", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["product_id"] == "P001"
    assert "current_stock" in data
    assert "average_stock" in data
    assert "estimated_days_of_stock" in data
    assert "stockout_risk" in data
    assert data["stockout_risk"] in ["High", "Medium", "Low"]
    assert "inventory_ratio_avg" in data

def test_analytics_customer(client):
    payload = {
        "start_date": "2025-01-01",
        "end_date": "2025-01-10",
        "product_id": "P001"
    }
    response = client.post("/api/v1/analytics/customer", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "average_ltv" in data
    assert "active_users" in data
    assert "mean" in data["active_users"]
    assert "max" in data["active_users"]
    assert "retention_rate_avg" in data
    assert "age_group_distribution" in data
    assert isinstance(data["age_group_distribution"], dict)

def test_analytics_marketing(client):
    payload = {
        "start_date": "2025-01-01",
        "end_date": "2025-01-10",
        "product_id": "P001"
    }
    response = client.post("/api/v1/analytics/marketing", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "total_marketing_spend" in data
    assert "average_roas" in data
    assert "average_ctr" in data
    assert "marketing_spend_to_revenue_ratio" in data
    assert "spend_revenue_correlation" in data

def test_analytics_pricing(client):
    payload = {
        "start_date": "2025-01-01",
        "end_date": "2025-01-10",
        "product_id": "P001"
    }
    response = client.post("/api/v1/analytics/pricing", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "average_price" in data
    assert "average_discount" in data
    assert "discount_buckets_performance" in data
    assert "price_elasticity_estimate" in data
    buckets = data["discount_buckets_performance"]
    for b in ["0-10%", "10-20%", "20-30%", "30%+"]:
        assert b in buckets
        detail = buckets[b]
        assert "average_price" in detail
        assert "average_orders" in detail
        assert "average_revenue" in detail
        assert "average_conversion_rate" in detail
        assert "sample_count" in detail
