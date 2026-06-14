import pytest

def test_agent_query_fallback_or_real(client):
    payload = {
        "query": "what will be my revenue next month?"
    }
    response = client.post("/api/v1/agent/query", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["query"] == "what will be my revenue next month?"
    assert "route_called" in data
    assert "raw_data" in data
    assert "response" in data
    assert isinstance(data["response"], str)
    assert len(data["response"]) > 0

def test_agent_query_scenario(client):
    payload = {
        "query": "what if i decrease discount by 5 and increase shipping by 20?"
    }
    response = client.post("/api/v1/agent/query", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "route_called" in data
    assert data["route_called"] == "scenario_evaluate"
    assert "raw_data" in data
    assert "response" in data
