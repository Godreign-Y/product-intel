# AI-Powered Business Analytics Assistant ML Microservice

A production-grade, modular, and completely independent ML microservice designed to serve as the intelligence engine for a business analytics chatbot. Built using **FastAPI**, **LightGBM**, **SHAP**, and **Pandas**.

The microservice operates as a standalone calculation engine. The LLM chatbot backend should query these APIs and synthesize the structured JSON responses into natural language for end-users, ensuring that the LLM never performs raw mathematical calculations.

---

## Technical Architecture

- **Independent Operations**: The service has no external dependencies on the chatbot backend. It exposes high-performance REST APIs.
- **LightGBM Forecast Estimators**: Trains 5 separate regressors (`revenue`, `profit`, `orders`, `conversion_rate`, `retention_rate`) using recursive multi-step forecasting with calendar, lag, and rolling statistics.
- **Explainability**: Leverages `shap.TreeExplainer` on the trained tree structures to return precise feature contributions (SHAP values) for any forecasting query.
- **Simulation**: Provides counterfactual simulation (what-if scenarios) by overriding future metrics and computing delta changes against baseline predictions.
- **Optimization**: Resolves pricing and discount optimizations using constrained multi-dimensional grid search over the trained models.

---

## Directory Layout

```
sprint2_product_intel/
├── config/             # Config files
├── data/               # CSV datasets (raw/processed)
├── models/             # Serialized .joblib models, preprocessors, and evaluation metrics
├── src/
│   ├── api/            # FastAPI Routers and Pydantic Schemas
│   ├── core/           # Core calculations (forecaster, explainer, analyzer, simulator, optimizer)
│   └── pipeline/       # Preprocessor and training script
├── tests/              # Pytest unit and integration suite
├── Dockerfile          # Production Dockerfile
├── docker-compose.yml  # Local Compose orchestrations
├── requirements.txt    # Python packages
└── run.py              # Local FastAPI runner
```

---

## Local Setup & Installation

### 1. Prerequisites
- Python 3.11+
- Virtualenv package

### 2. Environment Configuration
Create and activate a virtual environment, then install the dependencies:
```bash
# Create virtual environment
python -m venv venv

# Activate on Windows PowerShell
.\venv\Scripts\Activate.ps1

# Install package dependencies
pip install -r requirements.txt
```

### 3. Model Pipeline & Fast Training
The system uses the `temporal_dataset.csv` in the root folder as the training source. To train/re-train models and prepare explainers:
```bash
$env:PYTHONPATH="."
python src/pipeline/trainer.py
```
*(Runs in less than 5 seconds in fast mode to verify pipeline and produce testable models).*

### 4. Running the Microservice Locally
Launch the FastAPI development server:
```bash
python run.py
```
The interactive Swagger API documentation will be available at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## Docker Deployment

To run the containerized service in production:
```bash
# Build the Docker image
docker build -t ml-analytics-service .

# Run the container
docker run -p 8000:8000 ml-analytics-service
```
Or run with docker-compose:
```bash
docker-compose up --build -d
```

---

## API Integration Guide (Chatbot Integration)

Here are the REST API endpoints corresponding to the user queries:

### 1. Forecast Revenue Next Month
* **Endpoint**: `POST /api/v1/forecast/predict`
* **Payload**:
  ```bash
  curl -X POST "http://127.0.0.1:8000/api/v1/forecast/predict" \
       -H "Content-Type: application/json" \
       -d '{"target_metric": "revenue", "product_id": "P001", "horizon_days": 30}'
  ```

### 2. Why did revenue decrease? / Explain this forecast
* **Endpoint**: `POST /api/v1/explanation/explain`
* **Payload**:
  ```bash
  curl -X POST "http://127.0.0.1:8000/api/v1/explanation/explain" \
       -H "Content-Type: application/json" \
       -d '{"target_metric": "revenue", "product_id": "P001", "date": "2025-01-05"}'
  ```
* *Returns the SHAP attribution values explaining which features increased or decreased predicted values.*

### 3. What happens if discount increases by 5%?
* **Endpoint**: `POST /api/v1/scenario/simulate`
* **Payload**:
  ```bash
  curl -X POST "http://127.0.0.1:8000/api/v1/scenario/simulate" \
       -H "Content-Type: application/json" \
       -d '{"target_metric": "revenue", "product_id": "P001", "horizon_days": 30, "modifications": {"discount_pct": {"type": "add", "value": 5.0}}}'
  ```

### 4. How do I maximize revenue?
* **Endpoint**: `POST /api/v1/optimization/maximize`
* **Payload**:
  ```bash
  curl -X POST "http://127.0.0.1:8000/api/v1/optimization/maximize" \
       -H "Content-Type: application/json" \
       -d '{"target_metric": "revenue", "product_id": "P001", "horizon_days": 30, "max_discount_pct": 0.25, "max_marketing_budget": 200.0}'
  ```

### 5. Compare this month with last month
* **Endpoint**: `POST /api/v1/analysis/compare`
* **Payload**:
  ```bash
  curl -X POST "http://127.0.0.1:8000/api/v1/analysis/compare" \
       -H "Content-Type: application/json" \
       -d '{"period1_start": "2025-01-01", "period1_end": "2025-01-15", "period2_start": "2025-01-16", "period2_end": "2025-01-30", "product_id": "P001"}'
  ```

### 6. Which products are declining?
* **Endpoint**: `POST /api/v1/analysis/declining`
* **Payload**:
  ```bash
  curl -X POST "http://127.0.0.1:8000/api/v1/analysis/declining" \
       -H "Content-Type: application/json" \
       -d '{"lookback_days": 30, "metric": "revenue"}'
  ```
