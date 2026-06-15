# Database Schema Design — Product Intelligence OS

## Database: Neon PostgreSQL (Serverless)

**Connection**: Neon Pooler (ap-southeast-1)  
**Schema tracked by**: Alembic (`alembic/versions/`)  
**Current revision**: `aaf0b5d513e5` (Initial schema)

---

## Tables

### 1. `chat_sessions`

Stores AI Workspace conversational threads.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | VARCHAR(64) | PRIMARY KEY, INDEX | Unique session/thread ID |
| `title` | VARCHAR(255) | NOT NULL | Display name of the chat session |
| `created_at` | DATETIME | DEFAULT now() | Creation timestamp |

**Relationships**: One-to-many → `chat_messages`

---

### 2. `chat_messages`

Individual messages within a chat session (user + assistant turns).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | VARCHAR(64) | PRIMARY KEY, INDEX | Unique message ID |
| `session_id` | VARCHAR(64) | FK → `chat_sessions.id` ON DELETE CASCADE | Parent session reference |
| `role` | VARCHAR(20) | NOT NULL | `user` or `assistant` |
| `content` | TEXT | NOT NULL | Message body |
| `timestamp` | VARCHAR(32) | NOT NULL | Formatted time string |
| `suggestions` | JSON | NULLABLE | Follow-up action prompts from AI |
| `hypothesis` | JSON | NULLABLE | Causal ML hypothesis attached to response |

---

### 3. `experiments`

Causal ML experiment definitions and simulation results.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | VARCHAR(64) | PRIMARY KEY, INDEX | Unique experiment ID |
| `name` | VARCHAR(255) | NOT NULL | Display name |
| `objective` | VARCHAR(255) | NOT NULL | Business objective |
| `hypothesis` | TEXT | NOT NULL | Hypothesis under test |
| `primary_metric` | VARCHAR(100) | NOT NULL | Target KPI (revenue, profit, etc.) |
| `expected_outcome` | VARCHAR(100) | NULLABLE | Projected lift |
| `type` | VARCHAR(50) | NOT NULL | Experiment type (A/B Test, Scenario, etc.) |
| `status` | VARCHAR(30) | NOT NULL | `Running`, `Completed`, `Archived` |
| `created_at` | DATETIME | DEFAULT now() | Creation timestamp |
| `variables` | JSON | NOT NULL | List of modified variable definitions |
| `simulation_preview` | JSON | NULLABLE | ML simulation results (expectedImpact, confidenceScore, etc.) |

---

### 4. `recommendations`

Tracks implementation status of AI-generated growth recommendations.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | VARCHAR(64) | PRIMARY KEY, INDEX | Recommendation ID (e.g. `rec_1`) |
| `status` | VARCHAR(30) | NOT NULL | `Active`, `Implemented`, `Archived` |
| `applied_at` | DATETIME | NULLABLE | Timestamp when implemented |

---

### 5. `alembic_version` (System)

Alembic migration tracking table.

| Column | Type | Description |
|--------|------|-------------|
| `version_num` | VARCHAR(32) | Current migration revision ID |

---

## Data Sources

| Data | Source | Storage |
|------|--------|---------|
| Product analytics (36,500 rows) | `temporal_dataset.csv` | Local file → pandas DataFrame |
| Chat sessions & messages | User interactions | Neon PostgreSQL |
| Experiments & simulations | User-created | Neon PostgreSQL |
| Recommendations status | User actions | Neon PostgreSQL |
| ML models (LightGBM) | Pre-trained | `models/` directory (joblib) |

---

## Migration Commands

```bash
# Check current revision
uv run alembic current

# Generate new migration after model changes
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback one step
uv run alembic downgrade -1
```
