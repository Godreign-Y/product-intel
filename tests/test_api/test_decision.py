import pytest
from fastapi.testclient import TestClient
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import app
from src.core.history.storage.database import get_db, Base
from src.core.history.storage.models import Snapshot, Event, Experiment, Report
from src.core.decision.storage.models import DecisionContext, Hypothesis, ValidationResult, ConfidenceScore, Recommendation, ExperimentPlan

# Use the isolated test database
TEST_DATABASE_URL = "sqlite:///data/test_historical_repository.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app, raise_server_exceptions=True)

@pytest.fixture(scope="module")
def setup_decision_test_db():
    # Always drop and recreate test database tables
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    
    # 1. Seed snapshots
    snap = Snapshot(
        snapshot_date=datetime.date(2025, 1, 1),
        total_revenue=12000.0,
        total_profit=3500.0,
        total_orders=120,
        mean_conversion_rate=0.032,
        mean_retention_rate=0.88,
        total_marketing_spend=1000.0,
        total_inventory=450,
        avg_discount_pct=12.0,
        avg_price=100.0,
        summary="Baseline stable test snapshot.",
        channel_mix={"Amazon": 50.0, "Direct": 50.0},
        campaign_mix={"Spring_Sale": 100.0}
    )
    db.add(snap)
    
    # 2. Seed an event anomaly
    ev = Event(
        event_date=datetime.date(2025, 1, 1),
        product_id="P001",
        event_type="Conversion Drop Anomaly",
        severity="High",
        kpis_affected="mean_conversion_rate",
        reason="Fulfillment checkout delay.",
        business_impact="Negatively affected orders count.",
        confidence=0.95
    )
    db.add(ev)
    db.commit()
    db.close()
    yield

def test_ask_decision_engine_discount(setup_decision_test_db):
    response = client.post("/api/v1/decision/ask", json={
        "query": "What will happen to our revenue and profit if we increase discounts by 15%?",
        "product_id": "P001",
        "session_id": "test_session_123"
    })
    
    assert response.status_code == 200
    data = response.json()
    
    assert "context_id" in data
    assert "query" in data
    assert "explanation" in data
    assert "recommendations" in data
    assert "ranked_hypotheses" in data
    
    # Check that recommendations and hypotheses list have items
    assert len(data["ranked_hypotheses"]) > 0
    assert len(data["recommendations"]) > 0
    
    # Verify values inside the first recommendation
    rec = data["recommendations"][0]
    assert "recommendation_text" in rec
    assert "action_type" in rec
    assert "priority" in rec
    assert "rollback_strategy" in rec
    assert "confidence_score" in rec

def test_ask_decision_engine_shipping(setup_decision_test_db):
    response = client.post("/api/v1/decision/ask", json={
        "query": "Should we reduce shipping fees to improve conversion?",
        "product_id": "P001"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["recommendations"]) > 0
    
    # Ensure one recommendation is related to fulfillment or shipping
    action_types = [r["action_type"] for r in data["recommendations"]]
    assert any(a in ["FULFILLMENT_OPTIMIZATION", "PROMOTIONAL_CAMPAIGN", "PRICING_ADJUSTMENT"] for a in action_types)

def test_ask_decision_engine_fallback(setup_decision_test_db):
    response = client.post("/api/v1/decision/ask", json={
        "query": "Explain the recent performance drop.",
        "product_id": "P001"
    })
    
    assert response.status_code == 200
    data = response.json()
    # Fallback hypotheses generated from general indicators
    assert len(data["ranked_hypotheses"]) > 0
