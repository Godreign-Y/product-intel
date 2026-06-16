# AI-Powered Business Analytics Assistant ML Microservice

A production-grade, modular, and completely independent ML microservice designed to serve as the intelligence engine for a business analytics platform. Built using **FastAPI**, **LightGBM**, **SHAP**, **SQLAlchemy**, and **SentenceTransformers**.

The microservice operates as a standalone calculation and reasoning engine. The React frontend dashboard and LLM chatbot query these REST APIs to fetch structured analytics and decision plans, ensuring the LLM never performs mathematical computations.

---

## Technical Architecture

The service coordinates computations across several modules:
* **LightGBM Forecast Estimators**: Trains 5 separate regressors (`revenue`, `profit`, `orders`, `conversion_rate`, `retention_rate`) using recursive multi-step forecasting with calendar, lag, and rolling statistics.
* **Explainability**: Leverages `shap.TreeExplainer` on the trained tree structures to return precise feature contributions (SHAP values) for any forecasting query.
* **Simulation**: Provides counterfactual simulation (what-if scenarios) by overriding future metrics and computing delta changes against baseline predictions.
* **Optimization**: Resolves pricing and discount optimizations using constrained multi-dimensional grid search over the trained models.
* **Historical Intelligence Repository (Module 2)**: Tracks daily performance snapshots, statistical outlier events (Z-score anomalies), step-change experiments (A/B style), and compiles natural language markdown reports with vector embeddings for semantic search.
* **AI Decision Intelligence Engine / AI Scientist (Module 3)**: Reasons using the ML forecasters, sensitivity engines, and the historical intelligence repository to validate candidate hypotheses and generate prioritized business recommendations and A/B test pilot parameters.
* **LLM Planner Agent**: Orchestrates query routing and processes conversational chat panel interactions with automatic deterministic fallback parsers.

---

## Directory Layout

```
sprint2_product_intel/
├── config/                 # Config files
├── data/                   # SQLite database files (repository & test databases)
├── frontend/               # React client Dashboard and Chat UI
├── models/                 # Serialized .joblib models, preprocessors, and metadata
├── src/
│   ├── api/                # FastAPI Routers, Dependencies, and Pydantic Schemas
│   │   ├── routers/        # Endpoint routers (forecast, history, decision, agent, etc.)
│   │   └── schemas/        # Pydantic validation schemas
│   ├── core/               # Core intelligence calculators
│   │   ├── history/        # Module 2 memory engine (builders, detectors, retrievers, embeddings)
│   │   ├── decision/       # Module 3 decision engine (context, validation, scorers, recommendation)
│   │   ├── agent/          # LLM Planner Agent routing and synthesis orchestrator
│   │   └── ...             # Core forecast, SHAP, sensitivity, simulator, and optimizer
│   └── pipeline/           # Preprocessor and training script
├── tests/                  # Pytest unit and integration suite
├── Dockerfile              # Production Dockerfile
├── requirements.txt        # Python packages
└── run.py                  # Local FastAPI runner
```

---

## Local Setup & Installation

### 1. Prerequisites
- Python 3.11+
- Node.js (for frontend Dashboard)

### 2. Environment Configuration
Create and activate a virtual environment, then install dependencies:
```bash
# Create virtual environment
python -m venv myenv

# Activate on Windows PowerShell
.\myenv\Scripts\Activate.ps1

# Install package dependencies
pip install -r requirements.txt
```

Create a `.env` file in the root directory and supply your Nvidia API key (needed for LLM planning & explanation):
```env
NVIDIA_API_KEY="your-nvapi-key"
```

### 3. Model Pipeline & Fast Training
The system uses the `temporal_dataset.csv` in the root folder as the training source. To train/re-train models and prepare explainers:
```bash
$env:PYTHONPATH="."
python src/pipeline/trainer.py
```

### 4. Build & Seed the Historical Repository (Module 2)
Ingest the temporal business dataset, scan for outliers and experiments, synthesize reports, and compute SentenceTransformer vector embeddings:
```bash
$env:PYTHONPATH="."
python src/utils/seed_repository.py
```
This initializes the SQLite database at `data/historical_repository.db`.

### 5. Running the Microservice Locally
Launch the FastAPI development server:
```bash
python run.py
```
* The interactive Swagger API documentation will be available at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* The server will automatically initialize/check database tables on startup.

### 6. Running the Frontend Locally
```bash
cd frontend
npm install
npm run dev
```
The React frontend dashboard is available at: [http://localhost:3000](http://localhost:3000)

---

## API Integration Catalog

### 1. Conversational Agent Entrypoint (Chat Interface)
* **Endpoint**: `POST /api/v1/agent/query`
* **Payload**:
  ```json
  {
    "query": "Should we reduce shipping fees to improve conversion?"
  }
  ```
* *Automatically determines business intent, routes query to the Decision Engine, runs validation models, matches vector repository, and returns a rich markdown answer.*

### 2. AI Decision Engine ask Flow (Module 3)
* **Endpoint**: `POST /api/v1/decision/ask`
* **Payload**:
  ```json
  {
    "query": "What will happen to our revenue and profit if we increase discounts by 15%?",
    "product_id": "P001",
    "session_id": "discount_simulation_01"
  }
  ```
* *Runs the complete decision engine loop, compiling hypotheses validation matrices, confidence ratings, priority recommendations, rollback blueprints, and A/B test duration recommendations.*

### 3. Historical Intelligence Search (Module 2 Vector Retrieval)
* **Endpoint**: `POST /api/v1/history/search`
* **Payload**:
  ```json
  {
    "query": "pricing discount tests",
    "limit": 5
  }
  ```
* *Performs dense vector cosine similarity search on the report embedding records using the SentenceTransformer index.*

---

## Verification & Tests

To run the automated tests locally:
```bash
# Run all tests
python -m pytest

# Run Decision tests only
python -m pytest tests/test_api/test_decision.py

# Run Repository tests only
python -m pytest tests/test_api/test_repository.py
```
All tests verify endpoint contracts, payload typing, database updates, and routing fallbacks.
