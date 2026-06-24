ValidationEngine MVP is implemented per the locked plan (Option B). Summary:

## What was built

### New modules (`src/core/decision/validation/`)
| Module | Role |
|--------|------|
| `resolver.py` | Resolves `driver_variable`, KPIs, direction, shock % from hypothesis + query |
| `coherence.py` | Multi-KPI trade-off checks (discount ↑ orders ↑ profit ↓ = coherent) |
| `plausibility.py` | Flags implausible forecast magnitudes per driver/KPI bounds |
| `adjudicator.py` | Family-aware verdicts: `supported` / `inconclusive` / `contradicted` |

Also added `src/core/decision/normalization.py` — shared driver/KPI normalization (no LLM import chain).

### Rewritten `validator.py`
Runs 6 signals → normalizes each → adjudicates:

1. **Forecast** (0.35) — via `ScenarioSimulator.evaluate_scenario`, all affected KPIs  
2. **Sensitivity** (0.25) — `SensitivityEngine` with `target_metric`, cached per product/KPI  
3. **Correlation** (0.10) — best-lag 0–7d + MI  
4. **Causal** (0.10) — tertile ATE + normalized effect  
5. **Historical** (0.15) — past experiment evidence from retriever  
6. **SHAP** (0.05) — top-N feature rank check (flag-first)

Output includes `adjudication`, `signals`, `families`, `multi_kpi_coherence`, `plausibility`, plus backward-compatible `correlation` / `forecast_simulation` / etc.

### Family logic (Option B)
- `supported` needs **≥2 agreeing families**
- **Model + historical** is enough (experiments not required)
- Model-only agreement → `inconclusive` (no self-confirming)

### Downstream wiring
- **`DecisionManager`** — passes explainer, clears sensitivity cache per flow, feeds evidence into validate, persists adjudication in DB  
- **`SensitivityEngine`** — new `target_metric` param  
- **`ConfidenceScorer`** — uses adjudication + MI; verdict adjustments  
- **`HypothesisRanker`** — verdict rank multiplier; contradicted sorted lower  
- **`RecommendationEngine`** — uses `driver_col` from validation; A/B test when verdict ≠ supported or band ≠ high  

### Config (`config/decision_config.yaml`)
Added: signal weights, adjudication thresholds, plausibility bounds, cross-KPI expectations.

### Tests
`tests/test_decision/test_validator.py` — 6 tests passing (resolver, coherence, plausibility, adjudication Option B).

---

## Example validation output shape

```python
{
  "adjudication": {
    "verdict": "supported",
    "confidence_band": "medium",
    "family_agreement": 0.67,
    "supporting_families": ["model_based", "historical"],
    "summary": "..."
  },
  "driver_col": "marketing_spend",
  "change_pct_used": 15.0,
  "forecast_by_kpi": {"revenue": {"delta_pct": 8.2}, ...},
  "multi_kpi_coherence": {"coherent": true, "pattern": "expected_trade_off"},
  "plausibility": {"level": "plausible", "flags": []}
}
```

Contradicted hypotheses stay in the ranked list — they are not dropped.

If you want next steps, we can add integration tests against live forecaster data or tune plausibility bounds from your actual dataset distributions.