import pytest
from fastapi.testclient import TestClient
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import app
from src.core.history.storage.database import get_db, Base
from src.core.history.storage.models import Snapshot, Event, Experiment, Report, ReportEmbedding

# Use a separate isolated test database
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

client = TestClient(app)

@pytest.fixture(scope="module")
def setup_test_db():
    # Always drop and recreate test database tables to ensure clean, isolated tests
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    
    # Always seed test database with mock entries for consistent assertions
    if True:
        # Create a mock snapshot
        snap = Snapshot(
            snapshot_date=datetime.date(2025, 1, 1),
            total_revenue=15000.0,
            total_profit=3000.0,
            total_orders=150,
            mean_conversion_rate=0.025,
            mean_retention_rate=0.85,
            total_marketing_spend=1200.0,
            total_inventory=500,
            avg_discount_pct=10.0,
            avg_price=100.0,
            summary="Stable performance day.",
            top_products=[{"product_id": "P001", "revenue": 5000.0}],
            channel_mix={"Amazon": 40.0, "Website": 60.0}
        )
        db.add(snap)
        
        # Create a mock event
        ev = Event(
            event_date=datetime.date(2025, 1, 1),
            product_id="P001",
            event_type="Revenue Spike",
            severity="High",
            kpis_affected="revenue",
            reason="Holiday promotional surge.",
            business_impact="Drove incremental gross contributions.",
            confidence=0.95
        )
        db.add(ev)
        
        # Create a mock experiment
        exp = Experiment(
            experiment_id="EXP_PRI_P001_0101",
            type="Pricing Experiment",
            product_ids="P001",
            category="Skincare",
            brand="Core",
            start_date=datetime.date(2025, 1, 1),
            end_date=datetime.date(2025, 1, 14),
            before_metrics={"revenue": 1000.0, "profit": 200.0, "conversion_rate": 0.02, "orders": 50, "retention_rate": 0.8},
            after_metrics={"revenue": 1200.0, "profit": 250.0, "conversion_rate": 0.024, "orders": 60, "retention_rate": 0.82},
            change_summary="Price was reduced from $100 to $90.",
            improvement_pct=20.0,
            outcome="positive",
            confidence_score=0.94
        )
        db.add(exp)
        db.commit()
        
        # Create mock report
        rep = Report(
            experiment_id=exp.id,
            structured_json={
                "business_context": "Skincare price elasticity test.",
                "changes_made": "Price drop from $100 to $90.",
                "observed_kpi_changes": {"revenue": "+20.0%", "profit": "+25.0%"},
                "positive_effects": ["Volume increased"],
                "negative_effects": [],
                "learnings": "Highly elastic response on entry lines.",
                "recommendations": "Keep the lower price."
            },
            human_readable_text="# Pricing Experiment Audit Report\n\nLearnings: Highly elastic response on entry lines. Recommendations: Keep the lower price."
        )
        db.add(rep)
        db.commit()
        
        # Compute and add mock embedding
        from src.core.history.embeddings.encoder import SentenceTransformerEncoder
        encoder = SentenceTransformerEncoder()
        emb_vector = encoder.encode("Pricing Experiment Skincare core price drop from $100 to $90")
        
        emb = ReportEmbedding(
            report_id=rep.id,
            embedding=emb_vector,
            meta_data={
                "experiment_id": exp.experiment_id,
                "type": exp.type,
                "category": exp.category,
                "outcome": exp.outcome
            }
        )
        db.add(emb)
        db.commit()
        
    db.close()
    yield

def test_get_snapshots(setup_test_db):
    response = client.get("/api/v1/history/snapshots?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "snapshot_date" in data[0]
    assert "total_revenue" in data[0]

def test_get_events(setup_test_db):
    response = client.get("/api/v1/history/events?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "event_type" in data[0]
    assert "severity" in data[0]

def test_get_experiments(setup_test_db):
    response = client.get("/api/v1/history/experiments?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "experiment_id" in data[0]
    assert "outcome" in data[0]

def test_get_report_details(setup_test_db):
    # Retrieve experiment first
    exps_res = client.get("/api/v1/history/experiments?limit=1")
    exp_id = exps_res.json()[0]["id"]
    
    response = client.get(f"/api/v1/history/reports/{exp_id}")
    assert response.status_code == 200
    data = response.json()
    assert "structured_json" in data
    assert "human_readable_text" in data

def test_semantic_search(setup_test_db):
    response = client.post("/api/v1/history/search", json={
        "query": "pricing change skincare price drop",
        "limit": 3
    })
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) > 0
    assert "score" in data["results"][0]
    assert "experiment" in data["results"][0]

def test_similar_experiments(setup_test_db):
    response = client.post("/api/v1/history/similar", json={
        "category": "Skincare",
        "features": {"avg_selling_price": 95.0},
        "limit": 2
    })
    assert response.status_code == 200
    data = response.json()
    assert "matches" in data
    assert len(data["matches"]) > 0
    assert "similarity_score" in data["matches"][0]
    assert "experiment" in data["matches"][0]

def test_knowledge_insights_caching(setup_test_db):
    # First request: computes and caches
    response = client.get("/api/v1/history/insights?topic=pricing")
    assert response.status_code == 200
    data1 = response.json()
    assert data1["topic"] == "pricing"
    assert "synthesized_rules" in data1
    
    # Second request: loads from cache
    response2 = client.get("/api/v1/history/insights?topic=pricing")
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["cached"] is True

def test_agent_routing_history(setup_test_db):
    # Check if natural query maps to repository routes
    response = client.post("/api/v1/agent/query", json={
        "query": "Show previous pricing experiments learnings"
    })
    assert response.status_code == 200
    data = response.json()
    assert "route_called" in data
    # Should route to repository actions
    assert data["route_called"] in ["repository_search", "repository_extract"]
