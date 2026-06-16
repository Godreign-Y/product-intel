import json
import datetime
from sqlalchemy import Column, Integer, Float, String, Date, Text, ForeignKey, JSON
from sqlalchemy.types import TypeDecorator, TEXT
from sqlalchemy.orm import relationship
from src.core.history.storage.database import Base

try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False

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
    top_products = Column(JSON)
    worst_products = Column(JSON)
    largest_growth = Column(JSON)
    largest_decline = Column(JSON)
    inventory_alerts = Column(JSON)
    channel_mix = Column(JSON)
    campaign_mix = Column(JSON)
    traffic_mix = Column(JSON)
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
    product_ids = Column(String(500))  # Comma separated
    category = Column(String(100), index=True)
    brand = Column(String(100))
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    before_metrics = Column(JSON)
    after_metrics = Column(JSON)
    change_summary = Column(Text)
    improvement_pct = Column(Float)
    outcome = Column(String(50), index=True)  # positive, negative, neutral
    confidence_score = Column(Float)
    
    report = relationship("Report", uselist=False, back_populates="experiment", cascade="all, delete-orphan")

class Report(Base):
    __tablename__ = 'reports'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    experiment_id = Column(Integer, ForeignKey('experiments.id', ondelete="CASCADE"), nullable=False)
    structured_json = Column(JSON)
    human_readable_text = Column(Text)
    
    experiment = relationship("Experiment", back_populates="report")
    embeddings = relationship("ReportEmbedding", back_populates="report", cascade="all, delete-orphan")

class ReportEmbedding(Base):
    __tablename__ = 'report_embeddings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey('reports.id', ondelete="CASCADE"), nullable=False)
    embedding = Column(VectorType, nullable=False)  # 384 dimensions
    meta_data = Column(JSON)
    
    report = relationship("Report", back_populates="embeddings")

class KnowledgeBase(Base):
    __tablename__ = 'knowledge_base'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pattern_type = Column(String(100), nullable=False, index=True)
    query_context = Column(Text)
    synthesized_rules = Column(JSON)
    confidence_score = Column(Float)
    created_at = Column(Date, default=datetime.date.today)
