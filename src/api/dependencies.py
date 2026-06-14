import os
import pandas as pd
from functools import lru_cache
from typing import Generator, Optional, Any

from src.core.forecaster import ProductForecaster
from src.core.explainer import PredictionExplainer
from src.core.simulator import ScenarioSimulator
from src.core.optimizer import RevenueOptimizer
from src.core.analyzer import BusinessAnalyzer
from src.utils.logger import setup_logger

logger = setup_logger("dependencies")

# In-memory global cache for files that should load only once
class AppState:
    df_historical: Optional[pd.DataFrame] = None
    forecaster: Optional[ProductForecaster] = None
    explainer: Optional[PredictionExplainer] = None
    simulator: Optional[ScenarioSimulator] = None
    optimizer: Optional[RevenueOptimizer] = None
    analyzer: Optional[BusinessAnalyzer] = None
    analytics_engine: Optional[Any] = None
    sensitivity_engine: Optional[Any] = None
    planner_agent: Optional[Any] = None

def load_app_state(models_dir: str = "models", preprocessor_path: str = "models/preprocessor.joblib", csv_path: str = "temporal_dataset.csv"):
    if AppState.df_historical is None:
        logger.info(f"Loading historical dataset from {csv_path}...")
        AppState.df_historical = pd.read_csv(csv_path)
        AppState.df_historical["date"] = pd.to_datetime(AppState.df_historical["date"])
        logger.info(f"Historical dataset loaded. Row count: {len(AppState.df_historical)}")
        
    if AppState.forecaster is None:
        logger.info(f"Loading Forecaster from {models_dir}...")
        AppState.forecaster = ProductForecaster(models_dir, preprocessor_path)
        
    if AppState.explainer is None:
        logger.info("Loading SHAP Explainer...")
        AppState.explainer = PredictionExplainer(AppState.forecaster)
        
    if AppState.simulator is None:
        logger.info("Initializing Scenario Simulator...")
        AppState.simulator = ScenarioSimulator(AppState.forecaster)
        
    if AppState.optimizer is None:
        logger.info("Initializing Parameter Optimizer...")
        AppState.optimizer = RevenueOptimizer(AppState.forecaster)
        
    if AppState.analyzer is None:
        logger.info("Initializing Business Analyzer...")
        AppState.analyzer = BusinessAnalyzer()

    if AppState.analytics_engine is None:
        logger.info("Initializing Analytics Engine...")
        from src.core.analytics.engine import AnalyticsEngine
        AppState.analytics_engine = AnalyticsEngine(AppState.df_historical)

    if AppState.sensitivity_engine is None:
        logger.info("Initializing Sensitivity Engine...")
        from src.core.sensitivity import SensitivityEngine
        AppState.sensitivity_engine = SensitivityEngine(AppState.forecaster)

    if AppState.planner_agent is None:
        logger.info("Initializing LLM Planner Agent...")
        from src.core.agent.planner import LLMPlannerAgent
        AppState.planner_agent = LLMPlannerAgent(
            forecaster=AppState.forecaster,
            explainer=AppState.explainer,
            simulator=AppState.simulator,
            optimizer=AppState.optimizer,
            analyzer=AppState.analyzer,
            analytics_engine=AppState.analytics_engine,
            sensitivity_engine=AppState.sensitivity_engine,
            df_historical=AppState.df_historical
        )

def get_historical_data() -> pd.DataFrame:
    if AppState.df_historical is None:
        load_app_state()
    return AppState.df_historical

def get_forecaster() -> ProductForecaster:
    if AppState.forecaster is None:
        load_app_state()
    return AppState.forecaster

def get_explainer() -> PredictionExplainer:
    if AppState.explainer is None:
        load_app_state()
    return AppState.explainer

def get_simulator() -> ScenarioSimulator:
    if AppState.simulator is None:
        load_app_state()
    return AppState.simulator

def get_optimizer() -> RevenueOptimizer:
    if AppState.optimizer is None:
        load_app_state()
    return AppState.optimizer

def get_analyzer() -> BusinessAnalyzer:
    if AppState.analyzer is None:
        load_app_state()
    return AppState.analyzer

def get_analytics_engine():
    if AppState.analytics_engine is None:
        load_app_state()
    return AppState.analytics_engine

def get_sensitivity_engine():
    if AppState.sensitivity_engine is None:
        load_app_state()
    return AppState.sensitivity_engine

def get_planner_agent():
    if AppState.planner_agent is None:
        load_app_state()
    return AppState.planner_agent
