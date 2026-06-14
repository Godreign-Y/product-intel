from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.api.routers import forecast, explanation, scenario, optimization, analysis, analytics, sensitivity, agent
from src.api.dependencies import load_app_state
from src.utils.logger import setup_logger

logger = setup_logger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load and cache models, dataset, and explainers on startup
    logger.info("Initializing application models and dataset cache...")
    try:
        load_app_state()
        logger.info("Application state initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize application state: {e}")
    yield
    logger.info("Shutting down application...")

app = FastAPI(
    title="AI-Powered Business Analytics Assistant ML Microservice",
    description="Production-grade independent intelligence engine and ML microservice. Exposes forecasting, explainability, scenario simulations, and parameter optimizations.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for secure independent communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root status check
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "timestamp": "2026-06-14T21:00:00Z"
    }

# Register API Routers
app.include_router(forecast.router, prefix="/api/v1")
app.include_router(explanation.router, prefix="/api/v1")
app.include_router(scenario.router, prefix="/api/v1")
app.include_router(optimization.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(sensitivity.router, prefix="/api/v1")
app.include_router(agent.router, prefix="/api/v1")
