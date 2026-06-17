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
    anomaly_engine: Optional[Any] = None
    history_encoder: Optional[Any] = None
    llm_client: Optional[Any] = None

def get_historical_df_from_csv(
    start_date: Optional[Any] = None,
    end_date: Optional[Any] = None,
    product_id: Optional[str] = None,
    category: Optional[str] = None,
    csv_path: str = "temporal_dataset.csv"
) -> pd.DataFrame:
    if not os.path.exists(csv_path):
        logger.error(f"CSV path {csv_path} does not exist.")
        return pd.DataFrame()
        
    df = pd.read_csv(csv_path)
    df["date"] = pd.to_datetime(df["date"])
    
    if product_id:
        df = df[df["product_id"] == product_id]
    if category:
        df = df[df["category"] == category]
    if start_date:
        df = df[df["date"] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df["date"] <= pd.to_datetime(end_date)]
        
    df = df.sort_values(by=["product_id", "date"]).reset_index(drop=True)
    return df

def get_historical_df_from_db(
    start_date: Optional[Any] = None,
    end_date: Optional[Any] = None,
    product_id: Optional[str] = None,
    category: Optional[str] = None
) -> pd.DataFrame:
    db_url = os.getenv("NEON_URL") or os.getenv("DATABASE_URL")
    if db_url and not db_url.startswith("sqlite"):
        try:
            from src.core.history.storage.database import engine
            from sqlalchemy import text
            
            query = "SELECT * FROM product_performance WHERE 1=1"
            params = {}
            
            if product_id:
                query += " AND product_id = :product_id"
                params["product_id"] = product_id
                
            if category:
                query += " AND category = :category"
                params["category"] = category
                
            if start_date:
                if hasattr(start_date, "strftime"):
                    start_date_str = start_date.strftime("%Y-%m-%d")
                else:
                    start_date_str = str(start_date)
                query += " AND date >= :start_date"
                params["start_date"] = start_date_str
                
            if end_date:
                if hasattr(end_date, "strftime"):
                    end_date_str = end_date.strftime("%Y-%m-%d")
                else:
                    end_date_str = str(end_date)
                query += " AND date <= :end_date"
                params["end_date"] = end_date_str
            
            logger.info(f"Executing dynamic query on database: {query} with params: {params}")
            
            df = pd.read_sql(text(query), con=engine, params=params)
            
            if not df.empty:
                df["date"] = pd.to_datetime(df["date"])
                if "id" in df.columns:
                    df = df.drop(columns=["id"])
                df = df.sort_values(by=["product_id", "date"]).reset_index(drop=True)
            return df
        except Exception as e:
            logger.error(f"Database dynamic query failed: {e}. Falling back to CSV...")
            return get_historical_df_from_csv(start_date, end_date, product_id, category)
    else:
        # Try SQLite first, otherwise CSV
        try:
            from src.core.history.storage.database import engine
            from sqlalchemy import text
            query = "SELECT * FROM product_performance WHERE 1=1"
            params = {}
            if product_id:
                query += " AND product_id = :product_id"
                params["product_id"] = product_id
            if category:
                query += " AND category = :category"
                params["category"] = category
            if start_date:
                if hasattr(start_date, "strftime"):
                    start_date_str = start_date.strftime("%Y-%m-%d")
                else:
                    start_date_str = str(start_date)
                query += " AND date >= :start_date"
                params["start_date"] = start_date_str
            if end_date:
                if hasattr(end_date, "strftime"):
                    end_date_str = end_date.strftime("%Y-%m-%d")
                else:
                    end_date_str = str(end_date)
                query += " AND date <= :end_date"
                params["end_date"] = end_date_str
            
            df = pd.read_sql(text(query), con=engine, params=params)
            if not df.empty:
                df["date"] = pd.to_datetime(df["date"])
                if "id" in df.columns:
                    df = df.drop(columns=["id"])
                df = df.sort_values(by=["product_id", "date"]).reset_index(drop=True)
            return df
        except Exception as e:
            logger.info(f"SQLite/DB query failed or SQLite not initialized: {e}. Using CSV...")
            return get_historical_df_from_csv(start_date, end_date, product_id, category)

def get_max_date_from_db() -> pd.Timestamp:
    db_url = os.getenv("NEON_URL") or os.getenv("DATABASE_URL")
    if db_url and not db_url.startswith("sqlite"):
        try:
            from src.core.history.storage.database import engine
            from sqlalchemy import text
            with engine.connect() as conn:
                res = conn.execute(text("SELECT MAX(date) FROM product_performance")).scalar()
                if res:
                    return pd.to_datetime(res)
        except Exception as e:
            logger.error(f"Failed to get max date from db: {e}")
    try:
        from src.core.history.storage.database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            res = conn.execute(text("SELECT MAX(date) FROM product_performance")).scalar()
            if res:
                return pd.to_datetime(res)
    except Exception:
        pass
    try:
        df = pd.read_csv("temporal_dataset.csv", usecols=["date"])
        return pd.to_datetime(df["date"].max())
    except Exception:
        return pd.Timestamp.now()

def load_app_state(models_dir: str = "models", preprocessor_path: str = "models/preprocessor.joblib", csv_path: str = "temporal_dataset.csv"):
    # Startup preloading of the entire dataset is disabled to prevent latency.
    AppState.df_historical = None

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

    if AppState.anomaly_engine is None:
        logger.info("Initializing Anomaly Detection Engine...")
        from src.core.anomaly.engine import AnomalyDetectionEngine
        AppState.anomaly_engine = AnomalyDetectionEngine(
            forecaster=AppState.forecaster,
            explainer=AppState.explainer,
            df_historical=AppState.df_historical
        )

    if AppState.history_encoder is None:
        logger.info("Initializing History Encoder...")
        from src.core.history.embeddings.encoder import SentenceTransformerEncoder
        AppState.history_encoder = SentenceTransformerEncoder()

    # ── LangGraph Pipeline ───────────────────────────────────────────
    if AppState.llm_client is None:
        logger.info("Initializing LLM Client...")
        from src.core.llm import LLMClient
        AppState.llm_client = LLMClient()

    try:
        from src.core.agent.graph import init_graph, _compiled_graph
        if _compiled_graph is None:
            logger.info("Compiling LangGraph agent pipeline...")
            init_graph(
                llm_client=AppState.llm_client,
                engines={
                    "forecaster": AppState.forecaster,
                    "explainer": AppState.explainer,
                    "simulator": AppState.simulator,
                    "optimizer": AppState.optimizer,
                    "analyzer": AppState.analyzer,
                    "analytics_engine": AppState.analytics_engine,
                    "sensitivity_engine": AppState.sensitivity_engine,
                    "anomaly_engine": AppState.anomaly_engine,
                    "history_encoder": AppState.history_encoder,
                },
            )
    except Exception as e:
        logger.warning(f"LangGraph initialization failed (legacy mode will be used): {e}")

def get_historical_data() -> pd.DataFrame:
    # Query database dynamically on demand if called by legacy functions or tests
    return get_historical_df_from_db()

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

def get_anomaly_engine():
    if AppState.anomaly_engine is None:
        load_app_state()
    return AppState.anomaly_engine
