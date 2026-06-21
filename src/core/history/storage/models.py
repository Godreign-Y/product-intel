import json
import math
import datetime
from typing import Any
from sqlalchemy import Column, Integer, Float, String, Date, Text, ForeignKey, JSON
from sqlalchemy.types import TypeDecorator, TEXT
from sqlalchemy.orm import relationship
from src.core.history.storage.database import Base

try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False

def _sanitize_json_value(value: Any) -> Any:
    """
    Recursively sanitize values so JSON columns never contain NaN/Inf that
    PostgreSQL rejects during inserts.
    """
    if isinstance(value, dict):
        return {str(k): _sanitize_json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_sanitize_json_value(item) for item in value]

    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return None
        return value

    # Handle numpy scalar / pandas scalar variants if present.
    for attr in ("item",):
        try:
            value = value.item()
            break
        except Exception:
            pass

    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None

    if isinstance(value, datetime.datetime):
        return value.isoformat()
    if isinstance(value, datetime.date):
        return value.isoformat()

    # Best-effort fallback for any unsupported objects.
    try:
        json.dumps(value)
    except Exception:
        return str(value)

    return value

class SafeJSON(JSON):
    """
    JSON type that normalizes NaN/Inf values before binding.
    """
    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return _sanitize_json_value(value)

class VectorType(TypeDecorator):
    """
    Custom SQLAlchemy type that maps list/numpy array vector representation
    to PostgreSQL pgvector or standard serialized JSON text on SQLite.
    """
    impl = TEXT
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and HAS_PGVECTOR:
            return dialect.type_descriptor(Vector(384))
        return dialect.type_descriptor(TEXT)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql" and HAS_PGVECTOR:
            return value
        if isinstance(value, list):
            return json.dumps(value)
        try:
            import numpy as np
            if isinstance(value, np.ndarray):
                return json.dumps(value.tolist())
        except ImportError:
            pass
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql" and HAS_PGVECTOR:
            # pgvector returns Vector objects, convert to list
            return list(value)
        try:
            return json.loads(value)
        except Exception:
            return value

class Snapshot(Base):
    __tablename__ = 'snapshots'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_date = Column(Date, unique=True, nullable=False, index=True)
    total_revenue = Column(Float, nullable=False)
    total_profit = Column(Float, nullable=False)
    total_orders = Column(Integer, nullable=False)
    mean_conversion_rate = Column(Float, nullable=False)
    mean_retention_rate = Column(Float, nullable=False)
    total_marketing_spend = Column(Float, nullable=False)
    total_inventory = Column(Integer, nullable=False)
    avg_discount_pct = Column(Float, nullable=False)
    avg_price = Column(Float, nullable=False)
    
    # Store aggregated mixes and logs
    top_products = Column(SafeJSON)
    worst_products = Column(SafeJSON)
    largest_growth = Column(SafeJSON)
    largest_decline = Column(SafeJSON)
    inventory_alerts = Column(SafeJSON)
    channel_mix = Column(SafeJSON)
    campaign_mix = Column(SafeJSON)
    traffic_mix = Column(SafeJSON)
    summary = Column(Text)

class Event(Base):
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_date = Column(Date, nullable=False, index=True)
    product_id = Column(String(50), nullable=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)  # Info, Medium, High, Critical
    kpis_affected = Column(String(200))
    reason = Column(Text)
    business_impact = Column(Text)
    confidence = Column(Float, default=1.0)

class Experiment(Base):
    __tablename__ = 'experiments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(String(100), unique=True, nullable=False, index=True)
    type = Column(String(100), nullable=False, index=True)  # ab_test, pricing, funnel, etc.
    product_ids = Column(Text)  # Support large list of comma separated product IDs
    category = Column(String(100), index=True)
    brand = Column(String(100))
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    before_metrics = Column(SafeJSON)
    after_metrics = Column(SafeJSON)
    change_summary = Column(Text)
    improvement_pct = Column(Float)
    outcome = Column(String(50), index=True)  # positive, negative, neutral
    confidence_score = Column(Float)
    
    # Structured entities for granular historical learning queries
    driver = Column(String(100), index=True)
    segment = Column(String(100), index=True)
    season = Column(String(50), index=True)
    outcome_score = Column(Float)
    confidence = Column(Float)

    # Added ExperimentRecord fields for rebuilding the history engine
    product_id = Column(String(50), index=True, nullable=True)
    driver_delta = Column(Float, nullable=True)
    kpi_target = Column(String(100), index=True, nullable=True)
    kpi_before = Column(Float, nullable=True)
    kpi_after = Column(Float, nullable=True)
    ATE = Column(Float, nullable=True)
    p_value = Column(Float, nullable=True)
    hypothesis_text = Column(Text, nullable=True)
    
    # Additional fields from experiment_dataset.csv
    subcategory = Column(String(100))
    changed_features = Column(SafeJSON)
    primary_metric = Column(String(100))
    expected_direction = Column(String(50))
    observed_effect_pct = Column(Float)
    result = Column(String(50))
    notes = Column(Text)
    
    report = relationship("Report", uselist=False, back_populates="experiment", cascade="all, delete-orphan")

class Report(Base):
    __tablename__ = 'reports'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(Integer, ForeignKey('experiments.id', ondelete="CASCADE"), nullable=False, index=True)
    structured_json = Column(SafeJSON)
    human_readable_text = Column(Text)
    
    experiment = relationship("Experiment", back_populates="report")
    embeddings = relationship("ReportEmbedding", back_populates="report", cascade="all, delete-orphan")

class ReportEmbedding(Base):
    __tablename__ = 'report_embeddings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey('reports.id', ondelete="CASCADE"), nullable=False, index=True)
    embedding = Column(VectorType, nullable=False)  # 384 dimensions
    meta_data = Column(SafeJSON)
    
    report = relationship("Report", back_populates="embeddings")

class KnowledgeBase(Base):
    __tablename__ = 'knowledge_base'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pattern_type = Column(String(100), nullable=False, index=True)
    query_context = Column(Text)
    synthesized_rules = Column(SafeJSON)
    confidence_score = Column(Float)
    created_at = Column(Date, default=datetime.date.today)
    
    # Structured entities for granular historical learning queries
    driver = Column(String(100), index=True)
    segment = Column(String(100), index=True)
    season = Column(String(50), index=True)
    outcome_score = Column(Float)
    confidence = Column(Float)


class ProductPerformance(Base):
    __tablename__ = 'product_performance'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    product_id = Column(String(50), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    subcategory = Column(String(100), nullable=True)
    brand = Column(String(100), nullable=True)
    avg_ltv = Column(Float, nullable=True)
    dominant_age_group = Column(String(50), nullable=True)
    inventory_available = Column(Integer, nullable=True)
    avg_selling_price = Column(Float, nullable=True)
    discount_pct = Column(Float, nullable=True)
    shipping_fee = Column(Float, nullable=True)
    sales_channel_mix = Column(SafeJSON, nullable=True)
    campaign_mix = Column(SafeJSON, nullable=True)
    acquisition_mix = Column(SafeJSON, nullable=True)
    amazon_sales_pct = Column(Float, nullable=True)
    website_sales_pct = Column(Float, nullable=True)
    nykaa_sales_pct = Column(Float, nullable=True)
    mobile_app_sales_pct = Column(Float, nullable=True)
    search_campaign_pct = Column(Float, nullable=True)
    social_campaign_pct = Column(Float, nullable=True)
    email_campaign_pct = Column(Float, nullable=True)
    affiliate_campaign_pct = Column(Float, nullable=True)
    google_source_pct = Column(Float, nullable=True)
    instagram_source_pct = Column(Float, nullable=True)
    facebook_source_pct = Column(Float, nullable=True)
    email_source_pct = Column(Float, nullable=True)
    organic_source_pct = Column(Float, nullable=True)
    referral_source_pct = Column(Float, nullable=True)
    marketing_spend = Column(Float, nullable=True)
    traffic = Column(Float, nullable=True)
    active_users = Column(Float, nullable=True)
    current_ctr = Column(Float, nullable=True)
    current_roas = Column(Float, nullable=True)
    orders = Column(Float, nullable=True)
    revenue = Column(Float, nullable=True)
    profit = Column(Float, nullable=True)
    conversion_rate = Column(Float, nullable=True)
    retention_rate = Column(Float, nullable=True)


class ProductDailyFeature(Base):
    __tablename__ = 'product_daily_features'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    product_id = Column(String(50), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    subcategory = Column(String(100), nullable=True)
    brand = Column(String(100), nullable=True)
    
    # Raw/L1 features
    avg_ltv = Column(Float, nullable=True)
    dominant_age_group = Column(String(50), nullable=True)
    inventory_available = Column(Integer, nullable=True)
    avg_selling_price = Column(Float, nullable=True)
    discount_pct = Column(Float, nullable=True)
    shipping_fee = Column(Float, nullable=True)
    amazon_sales_pct = Column(Float, nullable=True)
    website_sales_pct = Column(Float, nullable=True)
    nykaa_sales_pct = Column(Float, nullable=True)
    mobile_app_sales_pct = Column(Float, nullable=True)
    search_campaign_pct = Column(Float, nullable=True)
    social_campaign_pct = Column(Float, nullable=True)
    email_campaign_pct = Column(Float, nullable=True)
    affiliate_campaign_pct = Column(Float, nullable=True)
    google_source_pct = Column(Float, nullable=True)
    instagram_source_pct = Column(Float, nullable=True)
    facebook_source_pct = Column(Float, nullable=True)
    email_source_pct = Column(Float, nullable=True)
    organic_source_pct = Column(Float, nullable=True)
    referral_source_pct = Column(Float, nullable=True)
    marketing_spend = Column(Float, nullable=True)
    traffic = Column(Float, nullable=True)
    active_users = Column(Float, nullable=True)
    current_ctr = Column(Float, nullable=True)
    current_roas = Column(Float, nullable=True)
    orders = Column(Float, nullable=True)
    revenue = Column(Float, nullable=True)
    profit = Column(Float, nullable=True)
    conversion_rate = Column(Float, nullable=True)
    retention_rate = Column(Float, nullable=True)
    
    # Normalized features per product (Z-scores)
    revenue_norm = Column(Float, nullable=True)
    profit_norm = Column(Float, nullable=True)
    orders_norm = Column(Float, nullable=True)
    traffic_norm = Column(Float, nullable=True)
    active_users_norm = Column(Float, nullable=True)
    marketing_spend_norm = Column(Float, nullable=True)
    avg_selling_price_norm = Column(Float, nullable=True)
    discount_pct_norm = Column(Float, nullable=True)
    shipping_fee_norm = Column(Float, nullable=True)
    conversion_rate_norm = Column(Float, nullable=True)
    retention_rate_norm = Column(Float, nullable=True)
    
    # L2 Lags (7d and 30d)
    revenue_lag7 = Column(Float, nullable=True)
    profit_lag7 = Column(Float, nullable=True)
    orders_lag7 = Column(Float, nullable=True)
    conversion_rate_lag7 = Column(Float, nullable=True)
    retention_rate_lag7 = Column(Float, nullable=True)
    discount_pct_lag7 = Column(Float, nullable=True)
    marketing_spend_lag7 = Column(Float, nullable=True)
    avg_selling_price_lag7 = Column(Float, nullable=True)
    shipping_fee_lag7 = Column(Float, nullable=True)
    
    revenue_lag30 = Column(Float, nullable=True)
    profit_lag30 = Column(Float, nullable=True)
    orders_lag30 = Column(Float, nullable=True)
    conversion_rate_lag30 = Column(Float, nullable=True)
    retention_rate_lag30 = Column(Float, nullable=True)
    discount_pct_lag30 = Column(Float, nullable=True)
    marketing_spend_lag30 = Column(Float, nullable=True)
    avg_selling_price_lag30 = Column(Float, nullable=True)
    shipping_fee_lag30 = Column(Float, nullable=True)
    
    # L2 Rolling stats (7d and 30d mean/std for 5 KPIs)
    revenue_roll_mean7 = Column(Float, nullable=True)
    revenue_roll_std7 = Column(Float, nullable=True)
    revenue_roll_mean30 = Column(Float, nullable=True)
    revenue_roll_std30 = Column(Float, nullable=True)
    
    profit_roll_mean7 = Column(Float, nullable=True)
    profit_roll_std7 = Column(Float, nullable=True)
    profit_roll_mean30 = Column(Float, nullable=True)
    profit_roll_std30 = Column(Float, nullable=True)
    
    orders_roll_mean7 = Column(Float, nullable=True)
    orders_roll_std7 = Column(Float, nullable=True)
    orders_roll_mean30 = Column(Float, nullable=True)
    orders_roll_std30 = Column(Float, nullable=True)
    
    conversion_rate_roll_mean7 = Column(Float, nullable=True)
    conversion_rate_roll_std7 = Column(Float, nullable=True)
    conversion_rate_roll_mean30 = Column(Float, nullable=True)
    conversion_rate_roll_std30 = Column(Float, nullable=True)
    
    retention_rate_roll_mean7 = Column(Float, nullable=True)
    retention_rate_roll_std7 = Column(Float, nullable=True)
    retention_rate_roll_mean30 = Column(Float, nullable=True)
    retention_rate_roll_std30 = Column(Float, nullable=True)
    
    # L2 Elasticity proxies
    discount_cvr_elasticity_7d = Column(Float, nullable=True)
    discount_cvr_elasticity_30d = Column(Float, nullable=True)
    price_orders_elasticity_7d = Column(Float, nullable=True)
    price_orders_elasticity_30d = Column(Float, nullable=True)
    shipping_cvr_elasticity_7d = Column(Float, nullable=True)
    shipping_cvr_elasticity_30d = Column(Float, nullable=True)
    marketing_revenue_elasticity_7d = Column(Float, nullable=True)
    marketing_revenue_elasticity_30d = Column(Float, nullable=True)
    
    # cyclical temporal encodings
    day_of_week = Column(Integer, nullable=True)
    month = Column(Integer, nullable=True)
    day_of_week_sin = Column(Float, nullable=True)
    day_of_week_cos = Column(Float, nullable=True)
    month_sin = Column(Float, nullable=True)
    month_cos = Column(Float, nullable=True)


class Pattern(Base):
    __tablename__ = 'patterns'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pattern_type = Column(String(100), nullable=False, index=True) # anomaly, trend, elasticity, seasonality
    product_id = Column(String(50), nullable=True, index=True)
    kpi = Column(String(100), nullable=True, index=True)
    date = Column(Date, nullable=True, index=True)
    severity = Column(String(20), nullable=True, index=True) # for anomalies: Medium, High, Critical
    value = Column(Float, nullable=True) # generic slope, pct_change, coefficient
    details = Column(SafeJSON, nullable=True) # holds specific metadata (reasons, n_valid_obs, etc.)
    created_at = Column(Date, default=datetime.date.today)

