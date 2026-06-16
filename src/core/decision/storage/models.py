import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from src.core.history.storage.database import Base

class DecisionContext(Base):
    __tablename__ = 'decision_contexts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    user_query = Column(String(500), nullable=False)
    retrieved_kpi_snapshot = Column(JSON, nullable=True)  # KPIs averages dict
    active_anomalies = Column(JSON, nullable=True)       # Anomalies details
    trend_metrics = Column(JSON, nullable=True)          # Linear growth metrics
    
    hypotheses = relationship("Hypothesis", back_populates="context", cascade="all, delete-orphan")

class Hypothesis(Base):
    __tablename__ = 'hypotheses'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    context_id = Column(Integer, ForeignKey('decision_contexts.id'), nullable=False)
    hypothesis_id = Column(String(100), unique=True, index=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    generated_from = Column(String(100), nullable=False)  # e.g., 'SHAP', 'Anomaly', 'Elasticity'
    affected_kpis = Column(JSON, nullable=True)           # affected metrics list
    confidence_prior = Column(Float, default=0.5)
    
    context = relationship("DecisionContext", back_populates="hypotheses")
    validation_results = relationship("ValidationResult", uselist=False, back_populates="hypothesis", cascade="all, delete-orphan")
    confidence_score = relationship("ConfidenceScore", uselist=False, back_populates="hypothesis", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="hypothesis", cascade="all, delete-orphan")

class ValidationResult(Base):
    __tablename__ = 'validation_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    hypothesis_id = Column(Integer, ForeignKey('hypotheses.id'), nullable=False)
    correlation_metrics = Column(JSON, nullable=True)    # Pearson, Spearman, MI
    forecast_sim_delta = Column(JSON, nullable=True)     # Forecast differences
    sensitivity_elasticity = Column(JSON, nullable=True)  # Elasticity derivatives
    causal_estimates = Column(JSON, nullable=True)       # Pluggable causal inference metrics
    segment_consistency = Column(JSON, nullable=True)    # Metrics consistency across segments
    
    hypothesis = relationship("Hypothesis", back_populates="validation_results")

class ConfidenceScore(Base):
    __tablename__ = 'confidence_scores'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    hypothesis_id = Column(Integer, ForeignKey('hypotheses.id'), nullable=False)
    overall_confidence = Column(Float, index=True, nullable=False)
    historical_agreement = Column(Float, default=0.0)
    correlation_strength = Column(Float, default=0.0)
    forecast_agreement = Column(Float, default=0.0)
    sensitivity_agreement = Column(Float, default=0.0)
    causal_confidence = Column(Float, default=0.0)
    data_quality_factor = Column(Float, default=0.0)
    reasoning_breakdown = Column(JSON, nullable=True)
    
    hypothesis = relationship("Hypothesis", back_populates="confidence_score")

class Recommendation(Base):
    __tablename__ = 'recommendations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    hypothesis_id = Column(Integer, ForeignKey('hypotheses.id'), nullable=False)
    recommendation_text = Column(Text, nullable=False)
    action_type = Column(String(100), nullable=False)      # e.g., 'PRICING_ADJUSTMENT'
    expected_kpi_improvement = Column(JSON, nullable=True) # e.g., {'revenue': '+5.2%'}
    estimated_roi = Column(Float, default=0.0)
    risk_assessment = Column(JSON, nullable=True)          # failure rates
    priority = Column(String(50), default='MEDIUM')        # 'HIGH', 'MEDIUM', 'LOW'
    rollback_strategy = Column(Text, nullable=True)
    
    hypothesis = relationship("Hypothesis", back_populates="recommendations")
    experiment_plan = relationship("ExperimentPlan", uselist=False, back_populates="recommendation", cascade="all, delete-orphan")

class ExperimentPlan(Base):
    __tablename__ = 'experiment_plans'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    recommendation_id = Column(Integer, ForeignKey('recommendations.id'), nullable=False)
    experiment_type = Column(String(100), nullable=False)  # e.g., 'A/B Test'
    suggested_duration_days = Column(Integer, default=14)
    required_sample_size = Column(Integer, default=1000)
    primary_metric = Column(String(100), nullable=False)
    success_criteria = Column(JSON, nullable=True)
    min_detectable_effect = Column(Float, default=0.05)
    
    recommendation = relationship("Recommendation", back_populates="experiment_plan")
