# AI-Powered Business Analytics Assistant - Monorepo

Welcome to the unified monorepo for the **AI-Powered Business Analytics Assistant**. This repository houses both the Fast API ML microservice (backend) and the React/Vite/TS dashboard (frontend).

## Repository Layout

```
Product_intel/
├── backend/            # Python FastAPI ML microservice (LightGBM, SHAP)
│   ├── src/            # Application logic and endpoints
│   ├── tests/          # Pytest integration/unit test suite
│   ├── requirements.txt# Python dependency specification
│   └── run.py          # Uvicorn FastAPI runner
├── frontend/           # React dashboard (Vite, TS, TailwindCSS v4)
│   ├── src/            # React pages, components, types, services
│   ├── package.json    # Node dependency specification
│   └── vite.config.ts  # Vite bundler config
├── package.json        # Root package.json orchestrating both environments
└── README.md           # This document
```

---

## Quickstart Setup

### 1. Prerequisites
- **Node.js** (v18+)
- **Python** (3.11+)
- **uv** (high-performance Python package manager, automatically configured)

### 2. Install and Setup Everything
From the root of this workspace, run:
```bash
npm install
npm run setup
```
This will automatically:
1. Install root dependencies (like `concurrently`).
2. Run `npm install` inside the `frontend/` directory.
3. Initialize the backend virtual environment using `uv venv` and install Python requirements.

---

## Run Development Servers

To run both the frontend and backend servers concurrently, run:
```bash
npm run dev
```

- **Frontend Development Server**: Runs on [http://localhost:3000](http://localhost:3000) (opens automatically)
- **Backend FastAPI Engine**: Runs on [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **FastAPI OpenAPI Swagger Docs**: Accessible at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## Helper Tasks

### Retraining backend ML models
To run the LightGBM models training pipeline on the dataset:
```bash
npm run train
```

### Running Backend Tests
To execute backend integration and unit tests:
```bash
npm run test:backend
```
