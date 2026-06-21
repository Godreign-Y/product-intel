import pytest
import datetime
import json
import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.history.storage.models import Base, ProductPerformance, Experiment, Report, ReportEmbedding
from src.core.history.manager import HistoryManager
from src.core.history.embeddings.encoder import SentenceTransformerEncoder
from src.core.decision.context.engine import ContextEngine
from src.core.sensitivity import SensitivityEngine
from src.core.forecaster import ProductForecaster

TEST_DB_URL = "sqlite:///data/test_history_rebuild.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=test_engine)

@pytest.fixture(scope="module")
def db():
    # Make sure we clean up test DB
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    yield session
    session.close()

@pytest.fixture(scope="module")
def setup_mock_csv():
    csv_path = "test_experiment_dataset.csv"
    data = [{
        "experiment_id": "EXP0001",
        "product_id": "P001",
        "category": "Skincare",
        "subcategory": "Serum",
        "brand": "Core",
        "experiment_type": "Pricing Experiment",
        "start_date": "2025-01-01",
        "end_date": "2025-01-14",
        "changed_features": '{"avg_selling_price": {"change_pct": 10.0, "new": 110.0, "old": 100.0}}',
        "primary_metric": "revenue",
        "expected_direction": "Increase",
        "observed_effect_pct": 15.0,
        "result": "Win",
        "confidence": 0.95,
        "notes": "Price increase led to revenue lift."
    }]
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    yield csv_path
    if os.path.exists(csv_path):
        os.remove(csv_path)

def test_history_manager_pipeline_and_query_api(db, setup_mock_csv):
    manager = HistoryManager(db)
    result = manager.run_build_pipeline(force_rebuild=True, csv_path=setup_mock_csv)
    
    assert result["status"] == "success"
    assert result["experiments_recorded"] == 1
    
    # Query Experiments
    exps = db.query(Experiment).all()
    assert len(exps) == 1
    assert exps[0].experiment_id == "EXP0001"
    assert exps[0].brand == "Core"
    assert exps[0].subcategory == "Serum"
    assert exps[0].notes == "Price increase led to revenue lift."
    
    # Query Reports
    reps = db.query(Report).all()
    assert len(reps) == 1
    assert "Executive Summary" in reps[0].human_readable_text
    
    # Query Embeddings
    embs = db.query(ReportEmbedding).all()
    assert len(embs) == 1
    
    # FAISS search
    search_res = manager.semantic_search("pricing increase skincare Core", limit=2)
    assert len(search_res) == 1
    assert search_res[0]["experiment"].experiment_id == "EXP0001"

def test_kpi_snapshot_from_performance_table(db):
    # Seed ProductPerformance
    perf = ProductPerformance(
        date=datetime.date(2025, 1, 1),
        product_id="P001",
        category="Skincare",
        subcategory="Serum",
        brand="Core",
        revenue=5000.0,
        profit=1000.0,
        orders=100,
        conversion_rate=0.02,
        retention_rate=0.8,
        discount_pct=10.0,
        avg_selling_price=50.0,
        amazon_sales_pct=50.0,
        website_sales_pct=50.0,
        nykaa_sales_pct=0.0,
        mobile_app_sales_pct=0.0,
        search_campaign_pct=100.0,
        social_campaign_pct=0.0,
        email_campaign_pct=0.0,
        affiliate_campaign_pct=0.0
    )
    db.add(perf)
    db.commit()
    
    manager = HistoryManager(db)
    snap = manager.get_kpi_snapshot("P001", window_days=7)
    assert snap["total_revenue"] == 5000.0
    assert snap["channel_mix"]["Amazon"] == 50.0

def test_decision_engines_integration(db):
    manager = HistoryManager(db)
    
    # Test ContextEngine pulling from ProductPerformance
    ctx_engine = ContextEngine(db, history_manager=manager)
    ctx = ctx_engine.assemble_context("skincare pricing check", "P001")
    assert ctx["kpis"]["total_revenue"] == 5000.0
    
    # Test SensitivityEngine perturbation fallback
    forecaster = ProductForecaster(models_dir="models", preprocessor_path="models/preprocessor.joblib")
    sens_engine = SensitivityEngine(forecaster)
    
    # Create temporal mock dataframe from temporal_dataset.csv
    df_hist = pd.read_csv("temporal_dataset.csv")
    df_hist = df_hist[df_hist["product_id"] == "P001"].head(15).copy()
    
    sens = sens_engine.calculate_sensitivity(df_hist, "P001", horizon_days=30)
    assert sens["discount"]["elasticity_score"] is not None
