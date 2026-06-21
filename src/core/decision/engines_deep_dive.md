# `src/core/decision` — Full File-by-File Deep Dive

> This module is the **Decision Intelligence Engine** — the "brain" of the platform. It orchestrates an **AI Scientist loop**: takes a plain-English business query, assembles real-time context, generates hypotheses using an LLM, validates them with ML tools, scores confidence, ranks, plans experiments, and delivers an executive-grade explanation.

---

## Directory Map

```
src/core/decision/
├── manager.py                  ← Orchestrator (the entry point)
├── storage/
│   └── models.py               ← SQLAlchemy DB schemas
├── context/
│   └── engine.py               ← Step 1: KPI + Anomaly + Trend assembler
├── hypothesis/
│   └── generator.py            ← Step 2: LLM/fallback candidate generator
├── evidence/
│   └── retriever.py            ← Step 3: Historical experiment evidence retriever
├── validation/
│   └── validator.py            ← Step 4: ML validation (correlation, sensitivity, forecast, causal)
├── confidence/
│   └── scorer.py               ← Step 5: Weighted confidence scorer
├── ranking/
│   └── ranker.py               ← Step 6: Rank by confidence × impact
├── recommendation/
│   └── engine.py               ← Step 7: Convert ranked items to actions
├── planner/
│   └── ab_planner.py           ← Step 8: A/B test plan generator
└── explanation/
    └── explainer.py            ← Step 9: Executive LLM/template brief generator
```

---

## Flow Diagram

```
User Query
    │
    ▼
[1] ContextEngine.assemble_context()
       KPIs + Anomalies + Trends
    │
    ▼
[2] HypothesisGenerator.generate_candidates()
       LLM (Llama 3.1 via NVIDIA NIM) → scored & pruned to top 5
    │
    ├──► [3] EvidenceRetriever.retrieve_historical_evidence()
    │         Semantic search on past experiments
    │
    ├──► [4] ValidationEngine.validate()
    │         Correlation + Sensitivity + Forecast Simulation + Causal
    │
    └──► [5] ConfidenceScorer.compute_confidence()
              Weighted composite score (0–0.99)
    │
    ▼
[6] HypothesisRanker.rank_hypotheses()
       Final ranking: 0.5 × confidence + 0.5 × impact
    │
    ▼
[7] RecommendationEngine.generate_recommendations()
       Action text, ROI proxy, priority, rollback strategy
    │
    ├──► [8] ExperimentPlanner.plan_experiment()  (only if confidence < 0.75)
    │         A/B test parameters: sample size, duration, MDE
    │
    ▼
[9] ExplanationEngine.generate_explanation()
       LLM or template Markdown executive brief
    │
    ▼
API Response (context_id, ranked_hypotheses, recommendations, explanation)
```

---

## 1. `manager.py` — The Orchestrator

**Role**: Wires all nine sub-engines together and executes `process_decision_flow()`. It is the single entry point called by the API router.

### Constructor (`__init__`)
Takes the DB session, historical DataFrame, and three ML engines:
- `ProductForecaster` — for counterfactual forecasting
- `SensitivityEngine` — for elasticity analysis
- `ScenarioSimulator` — for simulation

Has an **explainer fallback**: if no SHAP explainer is injected, it tries `AppState.explainer`. This matters because the `HypothesisGenerator` uses SHAP to prioritize which features to focus on.

### `process_decision_flow(query, product_id, session_id)`
This is **the AI Scientist loop** in a single method (195 lines). Here's what happens step by step:

1. **`ContextEngine.assemble_context(query)`** — pulls KPI snapshot + anomalies + trends from DB
2. **Saves `DecisionContext` to DB** with `session_id`, query, and the assembled context as JSON blobs
3. **`HypothesisGenerator.generate_candidates(context_data)`** — returns up to 5 scored candidates
4. **For each candidate** (serial loop — NOT truly parallel despite the "parallel" naming):
   - Makes hypothesis_id globally unique: `HYP_{context_id}_{original_id}`
   - Retrieves evidence via `EvidenceRetriever`
   - Runs full `ValidationEngine.validate()`
   - Computes `ConfidenceScorer.compute_confidence()`
   - **Writes all 3 objects** (Hypothesis, ValidationResult, ConfidenceScore) to DB immediately with `commit()`
5. **`HypothesisRanker.rank_hypotheses()`** — produces a sorted ranked list
6. **`RecommendationEngine.generate_recommendations()`** — generates action recommendations
7. **Saves Recommendations + optional ExperimentPlans** to DB for hypotheses that need A/B testing
8. **`ExplanationEngine.generate_explanation()`** — produces the final Markdown brief

### ⚠️ What's Static / Hardcoded
- `product_id` defaults to `"P001"` (L56) — meaning if the caller doesn't pass a product ID, all validation runs against product P001 only.
- DB commits happen **inside the hypothesis loop** (commit per hypothesis + final bulk commit). This means partial results can be saved even if a later hypothesis fails.
- The "parallel validation" in the docstring is **misleading** — it's entirely sequential.

---

## 2. `storage/models.py` — Database Schemas

**Role**: Defines all SQLAlchemy ORM tables for persisting the decision intelligence loop output.

### Tables and Their Purpose

| Table | What It Stores |
| :--- | :--- |
| `decision_contexts` | The top-level session: user query, KPI snapshot, anomalies, trends |
| `hypotheses` | Each generated hypothesis (title, description, driver, KPIs) |
| `validation_results` | The 4 validation outputs (correlation, forecast delta, sensitivity, causal) stored as JSON |
| `confidence_scores` | The 5-component weighted score breakdown per hypothesis |
| `recommendations` | Action text, action type, ROI estimate, rollback strategy, priority |
| `experiment_plans` | A/B test parameters: duration, sample size, MDE, success criteria |

### Relationships (Cascade Delete Chain)
```
DecisionContext
  └── Hypothesis (1:many)
        ├── ValidationResult (1:1)
        ├── ConfidenceScore (1:1)
        └── Recommendation (1:many)
              └── ExperimentPlan (1:1)
```

All relationships use `cascade="all, delete-orphan"` so deleting a context prunes everything.

### ⚠️ What's Static / Notable
- `hypothesis_id` has a `unique=True` constraint (L24). This is why `manager.py` adds `HYP_{context_id}_` prefix — to avoid DB constraint errors when the same template ID appears across sessions.
- `data_quality_factor` column on `ConfidenceScore` (L60) is defined in the DB but **never populated** by the scorer — it stays at 0.0. This is a gap/placeholder.
- `risk_assessment` on `Recommendation` (L74) is also defined but never written.

---

## 3. `context/engine.py` — Context Assembler

**Role**: Fetches live state from the DB to frame what's happening right now in the business.

### `get_latest_kpis()`
- Queries `Snapshot` model (from `history` module), orders by `snapshot_date DESC`, takes the **latest single snapshot**.
- Returns: `total_revenue`, `total_profit`, `total_orders`, `mean_conversion_rate`, `mean_retention_rate`, `avg_discount_pct`, `avg_price`, `channel_mix`, `campaign_mix`.
- **Fallback**: Returns all zeros if no snapshots exist.

### `get_recent_anomalies(limit=5)`
- Queries `Event` table, filtering only `severity IN ("High", "Critical")`.
- Returns: `date`, `product_id`, `event_type`, `severity`, `kpis_affected`, `reason`.

### `get_rolling_trends(days=30)`
Simple **half-period comparison** trend indicator:
1. Takes the last 30 snapshots
2. Splits them into first-half and second-half
3. Compares average revenue and orders: `(second_avg - first_avg) / first_avg`
4. Labels as `"increasing"` if >2%, `"decreasing"` if <-2%, else `"stable"`

### `assemble_context(query)`
Combines all three and adds timestamp. The `query` string itself is passed through but not actually analyzed at this stage — query understanding happens in the `HypothesisGenerator`.

### ⚠️ What's Static / Notable
- The trend threshold of ±2% is **hardcoded** (L84–85). There's no config for this.
- `get_latest_kpis()` returns **only a single day's snapshot**, not a rolling average. So the KPIs in context represent one day, not a period mean.
- The `query` parameter in `assemble_context` is included in the return dict but **not used** for any filtering or analysis within this engine.

---

## 4. `hypothesis/generator.py` — The LLM Hypothesis Generator

**Role**: The most complex file (418 lines). Produces 3–5 ranked candidate hypotheses using LLM or a fallback template bank.

### LLM Configuration
- Uses **Llama 3.1 70B Instruct** via **NVIDIA NIM API** (not OpenAI directly)
- Accessed via the OpenAI SDK pointing to `https://integrate.api.nvidia.com/v1`
- Requires `NVIDIA_API_KEY` in `.env`
- If the key is missing, the generator logs a warning and falls back to templates

### `generate_candidates(context)` — Main Method
Five-stage pipeline:
1. **`_determine_target_kpi(query)`** — keyword match: "profit/margin" → `profit`, "conversion/checkout" → `conversion_rate`, etc. Defaults to `"revenue"`.
2. **`_get_shap_features(target_kpi)`** — fetches SHAP global importance from the injected explainer. Returns empty list if no explainer.
3. **`_get_past_experiments(target_kpi)`** — queries `Experiment` table, returns 10 most recent as formatted strings.
4. **`_get_knowledge_base_rules()`** — queries `KnowledgeBase` table, returns 10 most recent rules as JSON strings.
5. Generates candidates via LLM (`_generate_llm_candidates`) or fallback (`_generate_fallback_candidates`).
6. **Scores every candidate** with `_score_candidate()` using a 4-factor composite.
7. **Sorts descending** by `generator_score` and **prunes to top 5**.
8. Strips scoring metadata before returning (to match the `DecisionManager` schema).

### `_generate_llm_candidates()` — LLM Prompt Design
**System prompt constraints enforced on LLM**:
- Hypothesis must map to one of 4 driver variables: `discount_pct`, `shipping_fee`, `avg_selling_price`, `marketing_spend`
- Must list one or more KPIs from: `total_revenue`, `total_profit`, `total_orders`, `mean_conversion_rate`
- Must include 7 specific fields per hypothesis
- Must return raw JSON array, no markdown wrapping
- Uses `temperature=0.3` (low temperature for consistent structured output), `max_tokens=1500`

**User prompt includes**: query, target KPI, current trends, active anomalies, SHAP importance, past experiments, KB rules.

**Parsing**: Extracts JSON using `re.search(r"\[.*\]", raw_text, re.DOTALL)` — extracts the first JSON array from the response. Falls back to direct `json.loads()` if regex finds nothing.

### `_generate_fallback_candidates()` — The 10 Static Templates
When LLM is unavailable, **10 hardcoded templates** cover 4 driver axes:

| ID | Driver | Title |
| :--- | :--- | :--- |
| `HYP_PRI_01` | `avg_selling_price` | Price increases decrease Customer Conversion |
| `HYP_PRI_02` | `avg_selling_price` | Optimal selling price drives higher Revenue |
| `HYP_DIS_01` | `discount_pct` | Higher discounts increase Order Volume |
| `HYP_DIS_02` | `discount_pct` | Excessive discounts erode net Profitability |
| `HYP_SHI_01` | `shipping_fee` | Shipping fee cuts improve Conversion Rate |
| `HYP_SHI_02` | `shipping_fee` | High shipping charges increase cart abandonment |
| `HYP_MKT_01` | `marketing_spend` | Increasing marketing spend drives Traffic and Revenue |
| `HYP_MKT_02` | `marketing_spend` | Diminishing ROAS on elevated Marketing Spend |
| `HYP_GEN_01` | `marketing_spend` | Sales declines are driven by Marketing budget cuts |
| `HYP_GEN_02` | `shipping_fee` | Fulfillment fee hikes depress profit margin |

**Query keyword filtering**: If the query contains "shipping", "discount", "price", or "marketing", the method returns only the matching driver's templates. Otherwise all 10 are returned.

### `_score_candidate()` — 4-Factor Composite
| Factor | Logic | Weight |
| :--- | :--- | :--- |
| Data Support | SHAP rank of driver: rank 1 = 1.0, rank 2 = 0.9, … none = 0.5 | 25% |
| Confidence | `confidence_prior` + 0.1 per matching past experiment (max +0.30) | 25% |
| Business Impact | 0.85 if revenue declining + marketing driver; 0.80 if discount; 0.75 if anomalies + shipping; else 0.5 | 25% |
| Explainability | 0.95 if description > 100 chars; 0.80 if > 50 chars; else 0.50 | 25% |

> **This is what's "static"**: the score is entirely rule-based. The LLM generates titles/descriptions, but the ranking and pruning are deterministic Python logic.

---

## 5. `evidence/retriever.py` — Historical Evidence Retriever

**Role**: Searches past experiments that are semantically similar to the current hypothesis title.

### `retrieve_historical_evidence(query, affected_kpis)`
- Delegates to `HistoryManager.semantic_search(query, limit=3)` — which does vector similarity search (TF-IDF or sentence embeddings depending on implementation).
- For each of the top 3 results, extracts:
  - `experiment_id`, `type`, `outcome` (`"positive"` / `"negative"`)
  - `improvement_pct`, `change_summary`
  - `learnings`, `recommendations` (from `report.structured_json`)
  - `semantic_similarity` score

### ⚠️ What's Static / Notable
- `affected_kpis` is received as a parameter but **never used** — the search is done only on the hypothesis title string.
- The `HistoryManager` is created as a fallback (`history_manager or HistoryManager(db)`) — so if none is injected, a new one is created (might miss in-memory state).
- Limit is hardcoded to 3 results — not configurable.

---

## 6. `validation/validator.py` — Multi-Method ML Validator

**Role**: Runs 4 independent statistical/ML validation checks against a hypothesis. The "parallel validation" claimed in the architecture is actually 4 sequential method calls.

### `run_correlation(kpi, driver, product_id)`
- Filters historical DataFrame to `product_id`
- Computes **Pearson** and **Spearman** correlations between `driver` and `kpi` columns
- Returns: `{ pearson, spearman, p_value }`
- Gracefully handles NaN values and exceptions

### `run_sensitivity_lookup(driver_key, product_id)`
- Maps driver keyword to sensitivity keys via a hardcoded dict:
  `"discount" → "discount"`, `"marketing"/"spend" → "marketing"`, `"retention"/"return" → "return"`, etc.
- Calls `SensitivityEngine.calculate_sensitivity()` and extracts the matching driver's results
- Returns: `{ elasticity_score, expected_impact, confidence }`

### `run_forecast_simulation(kpi, driver_col, change_pct, product_id)`
- Simulates a **±10% change** in the driver column (negative for "cut/reduce/lower" hypotheses)
- Runs two forecasts: baseline (no change) and perturbed (`current_features={driver_col: new_val}`) for a 14-day horizon
- Returns: `{ baseline_forecast, simulated_forecast, expected_delta, delta_pct }`
- **Type-safe**: casts the perturbed value to match the column's dtype (int if integer column)

### `run_causal_effect(kpi, driver, product_id)`
- Simple **ATE proxy**: median-splits the driver into "treatment" (above median) and "control" (below)
- Computes mean difference in KPI between treatment and control
- Validates with **Welch's T-test** (unequal variance)
- Returns: `{ ate_estimate, p_value, is_pluggable_ready, method }`
- Marked `is_pluggable_ready: True` as a signal that a proper causal model (DoWhy, CausalML) can replace this

### `validate(hypothesis, product_id)` — The Master Method
Driver and KPI resolution logic (all keyword-based):
- Hypothesis ID prefix `"SHI"` or title contains "shipping" → `driver_col = shipping_fee`
- Hypothesis ID prefix `"PRI"` or title contains "price/pricing" → `driver_col = avg_selling_price`
- Title contains "spend/marketing" → `driver_col = marketing_spend`
- Default → `discount_pct`

KPI column mapping:
- `"revenue" in kpi` → `revenue`
- `"profit" in kpi` → `profit`
- `"orders" in kpi` → `orders`
- `"conversion" in kpi` → `conversion_rate`
- Default → `revenue`

Has a **lazy DataFrame loader**: if `self.df` is None, calls `get_historical_df_from_db(product_id)`.

### ⚠️ What's Static / Notable
- `change_pct` is always ±10% — not informed by actual data variance or magnitude of observed anomaly.
- `daily_traffic_proxy = 150` in the A/B planner is hardcoded.
- Causal method is a naive median-split ATE, not a proper propensity score or IV approach — it's a known placeholder.

---

## 7. `confidence/scorer.py` — Confidence Scorer

**Role**: Aggregates 5 signal dimensions into one `overall_confidence` score (0.10–0.99).

### Weights (configurable, default):
| Signal | Default Weight |
| :--- | :--- |
| Historical Agreement | 15% |
| Correlation Strength | 20% |
| Sensitivity Alignment | 20% |
| Forecast Simulation Agreement | **25%** |
| Causal Confidence | 20% |

Forecast simulation has the highest weight because it reflects direct model evidence.

### Score Computation Per Signal

**Historical Agreement** (`hist_score`):
- 0.5 if no evidence found
- 0.90 if any past experiment had `outcome == "positive"`
- 0.60 if evidence found but no positive outcome

**Correlation Score** (`corr_score`):
- `abs(pearson + spearman) / 2` → bounded to `[0.10, 1.00]`

**Sensitivity Score** (`sens_score`):
- `min(1.0, abs(elasticity_score) * 2.0)` → bounded to `[0.10, 1.00]`

**Forecast Score** (`fore_score`):
- Checks **directional alignment**: if the hypothesis says "increase" but forecast shows a negative delta, score = 0.10 (penalty)
- If aligned: `min(1.0, abs(delta_pct) / 2.0)` bounded to `[0.20, 1.00]`

**Causal Score** (`causal_score`):
- `1 - p_value` → bounded to `[0.10, 1.00]`
- A p-value of 0.05 → causal_score = 0.95 (highly significant)

### ⚠️ What's Static / Notable
- The `weights` dict defaults are hardcoded but are **constructor-injectable** — the `DecisionManager` never injects custom weights, so they always use defaults.
- `overall_confidence` is capped at `0.99` (never 1.0) and floored at `0.10`.
- The reasoning string is always the same template — it doesn't vary based on which signals dominated.

---

## 8. `ranking/ranker.py` — Hypothesis Ranker

**Role**: Sorts validated hypotheses by a composite rank score.

### `rank_hypotheses(hypotheses, validation_results, confidence_scores)`
Simple scoring formula:
```python
rank_score = 0.5 * overall_confidence + 0.5 * min(1.0, abs(delta_pct) / 10.0)
```

The `impact_score` is capped by dividing `delta_pct` by 10, which means a 10%+ forecast change = full impact score. Anything below 1% barely contributes.

Returns each item as:
```python
{
    "hypothesis": hypo,
    "validation": val_res,
    "confidence": conf_score,
    "rank_score": rank_score,
    "estimated_impact_pct": delta_pct
}
```

### ⚠️ What's Static / Notable
- The 50/50 split between confidence and impact is **completely hardcoded** with no configuration knob.
- No normalization across the batch — items are ranked independently. Two hypotheses with the same `overall_confidence` and similar `delta_pct` will get very similar scores, making ordering non-deterministic.

---

## 9. `recommendation/engine.py` — Recommendation Engine

**Role**: Translates each ranked hypothesis into a business-readable action recommendation.

### `generate_recommendations(ranked_hypotheses)`
For each ranked item, produces:

**Action Type** (keyword-based):
| Condition | Action Type |
| :--- | :--- |
| "shipping" in id or title | `FULFILLMENT_OPTIMIZATION` |
| "spend" or "marketing" in title | `BUDGET_REALLOCATION` |
| "discount" in title | `PROMOTIONAL_CAMPAIGN` |
| Default | `PRICING_ADJUSTMENT` |

**Recommendation Text**: Template string that says "Proceed with +X% improvement" or "Review margin impacts carefully. Forecast suggests X% drop."

**Priority**:
- `rank_score >= 0.65` → `HIGH`
- `rank_score >= 0.45` → `MEDIUM`
- `rank_score < 0.45` → `LOW`

**Needs A/B Test**: `overall_confidence < 0.75` → requires experimentation before full rollout.

**Estimated ROI**: Absolute value of `expected_delta` from the forecast simulation (not a real ROI — it's a KPI delta proxy in whatever unit the KPI is measured).

**Rollback Strategy**: Template: "Rollback [action_type] settings to historical baselines if net margin drops below baseline control margins within 7 days."

### ⚠️ What's Static / Notable
- ALL of the above is **pure hardcoded logic**. There is no LLM involvement here.
- `rollback_strategy` is the same template for every recommendation, only `action_type` changes.
- The ROI is `abs(expected_delta)` — which is the raw KPI forecast delta, not actual financial ROI. For revenue forecasts this could be in thousands of dollars, but for conversion_rate it would be a tiny decimal.

---

## 10. `planner/ab_planner.py` — A/B Test Planner

**Role**: Generates A/B test parameters for recommendations that require experimentation.

### `plan_experiment(recommendation, primary_metric)`
Uses a **conservative power analysis heuristic** (not a proper scipy stats power calculation):
```python
variant_sample_size = int(3200 / ((mde_pct / 100.0) * 100.0) ** 2)
# With mde_pct = 5.0: variant_sample_size = int(3200 / 25) = 128
# Floored at 1000: variant_sample_size = 1000
# total = 2000
```

**Duration calculation**:
```python
duration_days = ceil(total_sample_size / 150)  # 150 = daily traffic proxy
# 2000 / 150 = ceil(13.3) = 14 days
# Bounded between 14 and 60 days
```

Returns:
- `experiment_type`: always "Two-Sample Independent A/B Test"
- `suggested_duration_days`: 14–60 days
- `required_sample_size`: 2000 (hardcoded outcome of the formula)
- `min_detectable_effect`: "5.0%"
- `success_criteria`: `{ metric, target_delta: "+5%", significance: "p < 0.05", power: "0.80" }`
- `rollback_trigger`: template string

### ⚠️ What's Static / Notable
- `mde_pct = 5.0` is **always 5%** — never derived from actual KPI variance or baseline conversion rates.
- `daily_traffic_proxy = 150` — **hardcoded**. For products with much higher/lower traffic this is meaningless.
- With the current formula, `required_sample_size` will **always be 2000** and `duration_days` will **always be 14** (because `ceil(2000/150) = 14`). The formula is a constant.

---

## 11. `explanation/explainer.py` — Executive Explanation Engine

**Role**: Final step — synthesizes all results into a polished Markdown executive brief.

### LLM Configuration
- Same NVIDIA NIM / Llama 3.1 70B setup as the `HypothesisGenerator`
- `temperature=0.2` (even more conservative — for professional, reproducible writing)
- `max_tokens=1000`
- **`timeout=10.0`** — only 10 seconds! If the LLM is slow, it falls back silently.

### `generate_explanation(ranked_items, recommendations)`
1. Compiles `summary_data` array with: hypothesis title, description, confidence score, expected impact, action text, A/B test flag, rollback strategy
2. If LLM is available, sends to Llama 3.1 with a system prompt requiring:
   - Executive Summary, Validated Hypotheses section, Action Recommendations
   - GitHub Markdown format with tables and bold text
   - Strict professional tone, no conversational fluff
3. On any exception (timeout, API error, etc.) → falls back to template

### `_generate_fallback_explanation(summary_data)` — The Template
Generates a clean 3-section Markdown document:

**Section 1 — Executive Summary**: States how many hypotheses were evaluated and how many have high confidence (≥0.70).

**Section 2 — Hypothesis & Validation Matrix**: A markdown table with:
- Hypothesis title (bold)
- Confidence score
- Expected KPI impact
- Action required ("A/B Test Pilot" or "Immediate Rollout")

**Section 3 — Detailed Recommendations**: For each hypothesis: rationale, tactical action text, rollback blueprint.

### ⚠️ What's Static / Notable
- The `ranked_items` and `recommendations` are correlated by **list index** (`recommendations[idx]`) — not by `hypothesis_id`. If the lists are ever out of sync, data will be mismatched.
- High confidence threshold (≥0.70) for "immediate rollout" is hardcoded.
- LLM timeout is only 10 seconds — aggressive for a 70B parameter model under load.

---

## Summary: What Is Actually Dynamic vs. Static

| Component | What's Dynamic (data-driven) | What's Static (hardcoded) |
| :--- | :--- | :--- |
| `context/engine.py` | KPIs, anomalies pulled from DB | ±2% trend threshold |
| `hypothesis/generator.py` | LLM generates custom hypotheses; SHAP ranks features | 10 fallback templates; 4-driver constraint; top-5 pruning |
| `evidence/retriever.py` | Semantic similarity search on live DB | Limit=3 hardcoded |
| `validation/validator.py` | Correlation, sensitivity, forecast, causal all computed live | ±10% change; keyword driver mapping |
| `confidence/scorer.py` | All 5 signals computed from live ML outputs | Weights (0.15/0.20/0.20/0.25/0.20) |
| `ranking/ranker.py` | confidence + impact from live data | 50/50 formula |
| `recommendation/engine.py` | Action text, ROI from live delta | All template strings, action type keyword map |
| `planner/ab_planner.py` | Nothing — pure formula | MDE=5%, traffic=150, always outputs 14d/2000 samples |
| `explanation/explainer.py` | LLM narrates live results | Fallback template; 10s timeout; index-based correlation |
