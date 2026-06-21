import pytest
from fastapi.testclient import TestClient
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

from src.api.main import app
from src.core.history.storage.database import get_db, Base
from src.core.history.storage.models import Snapshot, Event, Experiment, Report
from src.core.decision.storage.models import DecisionContext, Hypothesis, ValidationResult, ConfidenceScore, Recommendation, ExperimentPlan

@pytest.fixture(autouse=True)
def mock_llm_clients():
    with patch("src.core.decision.hypothesis.generator.OpenAI") as mock_openai_gen, \
         patch("src.core.decision.explanation.explainer.OpenAI") as mock_openai_exp, \
         patch("sentence_transformers.SentenceTransformer", side_effect=Exception("Mocked SentenceTransformer")):
        mock_openai_gen.return_value = None
        mock_openai_exp.return_value = None
        yield

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

def test_ask_decision_engine_determinism(setup_decision_test_db):
    results = []
    # Replay the query 10 times to verify that change_pct_used is identical across all runs
    for _ in range(10):
        response = client.post("/api/v1/decision/ask", json={
            "query": "What will happen to our revenue and profit if we increase discounts by 15%?",
            "product_id": "P001"
        })
        assert response.status_code == 200
        data = response.json()
        
        # Extract change_pct_used mapped by hypothesis_id
        changes = {}
        for item in data.get("ranked_hypotheses", []):
            hypo_id = item["hypothesis"]["hypothesis_id"]
            # Strip context ID to get base ID (e.g. HYP_9_HYP_DIS_03 -> HYP_DIS_03)
            parts = hypo_id.split("_")
            base_hypo_id = "_".join(parts[2:]) if len(parts) > 2 else hypo_id
            changes[base_hypo_id] = item["validation"].get("change_pct_used")
        results.append(changes)
        
    # Verify that change_pct_used values are identical across all 10 runs
    first_run = results[0]
    for idx, run in enumerate(results[1:], start=2):
        assert run == first_run, f"Non-deterministic change_pct_used detected on run {idx}: {run} vs {first_run}"

def test_risk_classifier_determinism():
    from src.core.decision.recommendation.risk_classifier import risk_classifier
    results = [
        risk_classifier.classify(confidence=0.4527, volatility="LOW", reversibility="EASY")
        for _ in range(50)
    ]
    assert len(set(results)) == 1
    assert results[0] == "High"  # confidence 0.4527 < 0.60 must always map to High


def test_parse_direction_word_boundaries():
    from src.core.decision.direction_utils import parse_direction
    # Boundary tests for false positives in substring matches
    assert parse_direction("This is supported by Experiment") == "neutral"
    assert parse_direction("A surprise increase in volume") == "positive"
    assert parse_direction("The enterprise discount drop") == "negative"
    assert parse_direction("We face a shortfall this quarter") == "neutral"
    assert parse_direction("The footfall declines") == "negative"


def test_direction_penalty_differentiation():
    from src.core.decision.confidence.scorer import ConfidenceScorer
    scorer = ConfidenceScorer()
    
    validation_results = {
        "correlation": {"pearson": 0.4, "spearman": 0.4},
        "sensitivity": {"elasticity_score": 0.5},
        "forecast_simulation": {"delta_pct": -8.5},  # negative outcome
        "causal": {"p_value": 0.02}
    }
    
    # 1. Contradicting title ("Marketing increases revenue") should receive a contradiction penalty
    score_contradict = scorer.compute_confidence(
        validation_results=validation_results,
        historical_evidence=[],
        title="Marketing spend increases revenue to maximize return",
        product_df_len=100,
        driver_keyword="marketing"
    )
    
    # 2. Aligned title ("Marketing decreases revenue") should score normally
    score_aligned = scorer.compute_confidence(
        validation_results=validation_results,
        historical_evidence=[],
        title="Marketing spend decreases revenue to maximize return",
        product_df_len=100,
        driver_keyword="marketing"
    )
    
    # Assert that contradiction receives lower score
    assert score_contradict["breakdown"]["forecast_simulation_agreement"] == 10.0
    assert score_aligned["breakdown"]["forecast_simulation_agreement"] > 10.0
    assert score_contradict["overall_confidence"] < score_aligned["overall_confidence"]


def test_neutral_direction_behavior(setup_decision_test_db):
    # Query without a direction should fallback to IQR-based calculation
    response = client.post("/api/v1/decision/ask", json={
        "query": "What happens if we change discounts?",
        "product_id": "P001"
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data["ranked_hypotheses"]) > 0
    # The default validation shock should be a fallback (e.g. not 0)
    assert data["ranked_hypotheses"][0]["validation"]["change_pct_used"] != 0.0

    # Test scorer neutral default (50.0)
    from src.core.decision.confidence.scorer import ConfidenceScorer
    scorer = ConfidenceScorer()
    validation_results = {
        "correlation": {"pearson": 0.4, "spearman": 0.4},
        "sensitivity": {"elasticity_score": 0.5},
        "forecast_simulation": {"delta_pct": -8.5},
        "causal": {"p_value": 0.02}
    }
    score_neutral = scorer.compute_confidence(
        validation_results=validation_results,
        historical_evidence=[],
        title="Discounts are modified for the product line",
        product_df_len=100,
        driver_keyword="discount"
    )
    assert score_neutral["breakdown"]["forecast_simulation_agreement"] == 50.0


def test_literal_shock_idempotency(setup_decision_test_db):
    results = []
    # Replay same query 10 times to verify that change_pct_used is stable and identical (should be 15.0 or -15.0 depending on query)
    for _ in range(10):
        response = client.post("/api/v1/decision/ask", json={
            "query": "What if we increase discounts by 15%?",
            "product_id": "P001"
        })
        assert response.status_code == 200
        data = response.json()
        
        # Verify first recommendation/hypothesis change_pct_used
        changes = {}
        for item in data.get("ranked_hypotheses", []):
            hypo_id = item["hypothesis"]["hypothesis_id"]
            parts = hypo_id.split("_")
            base_hypo_id = "_".join(parts[2:]) if len(parts) > 2 else hypo_id
            changes[base_hypo_id] = item["validation"].get("change_pct_used")
        results.append(changes)
        
    first_run = results[0]
    # Check that for discount_pct hypotheses, it matches the literal shock (15.0)
    assert any(val == 15.0 for val in first_run.values()), f"Literal shock 15.0 not used in: {first_run}"
    for idx, run in enumerate(results[1:], start=2):
        assert run == first_run, f"Non-deterministic query response detected: run {idx} != run 1"


def test_primary_vs_related_brief_layout():
    from src.core.decision.explanation.explainer import ExplanationEngine
    explainer = ExplanationEngine()
    
    summary_data = [
        {
            "hypothesis": "Discount increases revenue",
            "description": "Blah",
            "is_primary": True,
            "confidence_score": 0.8,
            "expected_impact": {"revenue": "+5.0%"},
            "action_recommended": "Increase discounts",
            "needs_ab_test": False,
            "rollback_strategy": "revert",
            "risk_assessment": {"volatility": "LOW", "reversibility": "EASY", "data_confidence": 0.8, "impact_magnitude": 5.0}
        },
        {
            "hypothesis": "Marketing boosts revenue",
            "description": "Blah",
            "is_primary": False,
            "confidence_score": 0.65,
            "expected_impact": {"revenue": "+2.0%"},
            "action_recommended": "Increase marketing",
            "needs_ab_test": True,
            "rollback_strategy": "revert",
            "risk_assessment": {"volatility": "LOW", "reversibility": "EASY", "data_confidence": 0.65, "impact_magnitude": 2.0}
        }
    ]
    
    brief = explainer._generate_fallback_explanation(summary_data)
    assert "Primary Opportunities" in brief
    assert "Related Opportunities" in brief
    assert "### Primary Recommendations" in brief
    assert "### Related Opportunity Recommendations" in brief
    assert "### Primary Opportunities Risk" in brief
    assert "### Related Opportunities Risk" in brief
