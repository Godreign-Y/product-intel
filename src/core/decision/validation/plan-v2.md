Your modifications are sound. Below is the **revised plan** with your changes integrated — this is the version I'd implement from.

---

# ValidationEngine Upgrade Plan (v2)

## Locked decisions (from your answers)

| Question | Decision |
|----------|----------|
| Contradicted hypotheses | **Keep always**, rank lower, never filter out |
| Sensitivity elasticity | **Extend `SensitivityEngine`** with `target_metric` — single source of truth |
| SHAP | **Top 5 hypotheses only**, weight ≤ 0.05, primarily a quality flag |
| Cross-KPI rules | **Yes, MVP** — 5 drivers: discount, price, marketing, inventory, shipping |
| Agreement threshold | **2-of-N** for `supported`, never 3-of-N at launch |

---

## Design principles (updated)

1. **Actionability over association** — forecast + elasticity dominate; correlation is supporting evidence only  
2. **Family independence** — model signals don't count as three independent votes  
3. **Economics-aware** — multi-KPI trade-offs are expected, not contradictions  
4. **Plausibility guardrail** — absurd effect magnitudes get flagged, not blindly trusted  
5. **Strict but survivable** — weak evidence → `inconclusive`; hard `contradicted` needs cross-family disagreement  

---

## Signal architecture

### Two layers of evidence

```
Layer A — Signal families (independence)
  model_based:   forecast, sensitivity, shap
  historical:    correlation, causal
  empirical:     past experiments

Layer B — Individual signals (within family)
  Each returns: direction, strength, confidence, direction_match, status
```

### Revised weights

```yaml
validation:
  signal_weights:
    forecast: 0.35
    sensitivity: 0.25
    historical: 0.15      # past experiments
    causal: 0.10
    correlation: 0.10
    shap: 0.05            # cap; often demoted to flag-only
```

**Rationale:** Decision-oriented signals (forecast + sensitivity = 60%) drive the score. Observational signals (correlation + causal = 20%) temper but don't dominate. SHAP is tie-break / flag, not a pillar.

### Family caps (prevents false confidence)

When adjudicating, apply **family-level deduplication**:

| Rule | Effect |
|------|--------|
| `model_based` family | At most **one family vote** toward agreement — derived from the **strongest** of forecast / sensitivity / shap (forecast wins ties) |
| `historical` family | Correlation and causal each count, but **both must not be required** — either can satisfy the historical slot |
| `empirical` family | Past experiments = independent vote; can satisfy one of the two required for `supported` |

**Family agreement formula (conceptual):**

```
family_votes = {
  model_based:  best_signal(forecast, sensitivity, shap) → agree | disagree | inconclusive
  historical:   aggregate(correlation, causal) → at least one must agree for family to count
  empirical:    experiments → agree | disagree | inconclusive
}

families_agreeing = count(family_votes == agree)
families_contradicting = count(family_votes == disagree)
```

**`supported` requires:**
- `families_agreeing ≥ 2` (not `signals_agreeing ≥ 2`)
- At least one agreeing family is **not** `model_based` *or* empirical experiments agree (prevents "model agrees with itself" → supported)

**Stricter variant (recommended):**

```
supported requires:
  - families_agreeing >= 2
  - AND (empirical == agree OR historical == agree)
  - AND model_based != contradict
```

So: model can support, but **can't carry the verdict alone**. You need historical or empirical backing. This matches your independence concern without being so strict that good hypotheses die.

---

## Revised pipeline

```
validate(hypothesis, context, evidence, query_pcts)
  │
  ├─ 0. RESOLVE          driver, KPIs, direction, shock (from driver_variable)
  ├─ 0b. MULTI-KPI       cross-KPI expectation check  ← MVP (moved up)
  │
  ├─ 1. FORECAST         ScenarioSimulator, primary + secondary KPIs
  ├─ 2. SENSITIVITY      SensitivityEngine(target_metric=kpi) [cached per product]
  ├─ 3. CORRELATION      best-lag Pearson/Spearman/MI, significance-aware
  ├─ 4. CAUSAL           tertile ATE + direction_match
  ├─ 5. EXPERIMENTS      from evidence retriever (already fetched)
  ├─ 6. SHAP             top-5 hypotheses only → rank check → flag or 0.05 weight
  │
  ├─ 7. PLAUSIBILITY     BusinessPlausibilityCheck (sanity layer)
  │
  └─ 8. ADJUDICATE       family_agreement + signal_agreement + verdict
```

---

## Phase 0 — MVP foundation

### 0.1 Hypothesis resolver
- `driver_variable` → `driver_col` (no title guessing)
- All `affected_kpis` normalized
- `expected_direction` from `direction_utils`
- Shock sizing: query literal → config min delta → IQR, clipped

### 0.2 Data hygiene
- Sort by date, `n_obs`, `insufficient_data` status (not fake zeros)

### 0.3 Multi-KPI coherence (MVP — your Issue 5)

**Cross-KPI expectation table** (config, 5 drivers):

| Driver | Primary KPI often | Secondary KPI typical relationship |
|--------|-------------------|----------------------------------|
| `discount_pct` | orders ↑ | profit may ↓ (expected trade-off) |
| `avg_selling_price` | revenue ↑ | orders may ↓ |
| `marketing_spend` | revenue ↑ | profit lagging / mixed |
| `shipping_fee` | conversion ↓ when fee ↑ | orders ↓ |
| `inventory_available` | orders ↑ when stock ↑ | revenue follows orders |

**Output:**

```python
"multi_kpi_coherence": {
  "coherent": true,
  "pattern": "expected_trade_off",  # or "aligned", "unexpected_conflict"
  "details": {
    "orders": {"delta_pct": +12, "expected": "positive", "match": true},
    "profit": {"delta_pct": -4, "expected": "negative_or_mixed", "match": true}
  }
}
```

**Strictness:** `unexpected_conflict` (e.g. discount ↑, orders ↓ 80%) → plausibility + coherence flags, **not** auto-`contradicted` unless forecast family also disagrees on primary KPI.

---

## Phase 1 — Core signals (MVP)

### 1.1 Forecast (0.35) — via `ScenarioSimulator`
- Primary + secondary KPI deltas
- `negligible_effect_pct: 2.0` → inconclusive, not contradict
- Direction match vs hypothesis

### 1.2 Sensitivity (0.25) — extend `SensitivityEngine`
- New param: `target_metric: str` (revenue, profit, orders, conversion_rate, retention_rate)
- Perturb driver → measure impact on **that** KPI's forecast sum/mean
- Cache: one call per `(product_id, horizon, target_metric)` per decision flow
- Validator reads slice for `driver_key` only

### 1.3 Correlation (0.10)
- Best lag 0–7d
- Significant opposite correlation → historical family `disagree`
- Weak / insignificant → `inconclusive` for that signal

### 1.4 Causal (0.10)
- ATE sign + `p_value`
- `p > 0.10` → inconclusive (not reject)

### 1.5 Experiments (0.15)
- Reuse evidence from `EvidenceRetriever`
- Match driver + KPI overlap
- `success_rate`, avg `improvement_pct`, direction consistency

### 1.6 SHAP (0.05 max, top 5 only)
- Only if hypothesis in top 5 post-generator prune
- If driver in top-N features → `shap_aligned: true`, small weight contribution
- If not → `quality_flag: weak_model_feature_support` (no score penalty beyond flag)
- **Never** a family vote on its own — rolls into `model_based` family as weakest of the three

---

## Phase 2 — Business plausibility (your Issue 4)

New: `BusinessPlausibilityCheck`

Runs **after** signals, **before** final verdict. Uses forecast deltas + driver-specific bounds from config.

**Examples:**

| Scenario | Plausibility |
|----------|--------------|
| discount ↑ 15%, orders +8% | `plausible` |
| discount ↑ 15%, orders −5% | `unusual` (flag, not reject) |
| discount ↑ 15%, orders −80% | `implausible` |
| shipping +50%, revenue +80% | `implausible` |

**Implementation sketch:**
- Per driver: max reasonable `|delta_pct|` per KPI from config or historical P99 of observed elasticities
- `implausible` → force confidence band to `low`, add flag, **cannot** reach `supported` with `high` band
- Does **not** alone produce `contradicted` — downgrades and flags

```yaml
validation:
  plausibility_bounds:
    discount_pct:
      orders: { max_positive: 50, max_negative: 30 }
      profit: { max_positive: 20, max_negative: 40 }
    shipping_fee:
      conversion_rate: { max_positive: 15, max_negative: 40 }
```

Tune from data over time.

---

## Phase 3 — Adjudication (revised)

### Verdict rules

```
SUPPORTED:
  - families_agreeing >= 2
  - at least one of {historical, empirical} agrees (not model-only)
  - model_based family != contradict
  - plausibility != implausible
  - primary KPI forecast direction_match == true (or negligible → inconclusive on forecast only)

INCONCLUSIVE:
  - families_agreeing == 1
  - OR agreement borderline (0.45–0.59 family score)
  - OR plausibility == unusual
  - OR insufficient data on majority of families

CONTRADICTED:
  - families_contradicting >= 2
  - OR (model_based == contradict AND historical == disagree)
  - OR primary KPI forecast strongly opposes with |delta| >= negligible threshold
  - Keep in output, rank lower
```

**2-of-N at family level**, with the empirical/historical backstop so the model can't self-confirm.

### Output shape

```python
{
  "signals": { ... },
  "families": {
    "model_based": {"vote": "agree", "driver_signal": "forecast", ...},
    "historical": {"vote": "inconclusive", ...},
    "empirical": {"vote": "agree", "success_rate": 0.75, ...}
  },
  "multi_kpi_coherence": { ... },
  "plausibility": {"level": "plausible", "flags": []},
  "adjudication": {
    "verdict": "supported",
    "confidence_band": "high",
    "family_agreement": 0.67,
    "signal_agreement": 0.72,   # informational, not primary
    "supporting_families": ["model_based", "empirical"],
    "quality_flags": [],
    "summary": "..."
  }
}
```

### Ranking impact
- `supported` + `high` → normal rank weight  
- `inconclusive` → rank middle, force `needs_experimentation`  
- `contradicted` → rank lower (multiply rank_score × 0.5), **still visible** in brief under "Contradicted / Low Confidence"

---

## Implementation order (MVP scope)

| Step | Deliverable |
|------|-------------|
| **1** | Resolver + data hygiene + insufficient_data semantics |
| **2** | Multi-KPI coherence table (5 drivers) + config |
| **3** | `SensitivityEngine.calculate_sensitivity(target_metric=...)` + cache in `DecisionManager` |
| **4** | Forecast via `ScenarioSimulator` |
| **5** | Correlation (lag) + causal + experiments wiring |
| **6** | SHAP for top 5 only, flag-first |
| **7** | `BusinessPlausibilityCheck` + bounds config |
| **8** | Adjudication with **family_agreement** + revised weights |
| **9** | Downstream: `ConfidenceScorer`, `Ranker`, `RecommendationEngine` read `adjudication` |
| **10** | Unit tests: family logic, coherence trade-offs, plausibility edge cases |

Steps 1–8 = shippable MVP. 9–10 = same PR or fast follow.

---

## What changed from v1 → v2 (your edits)

| Area | v1 | v2 |
|------|----|----|
| Weights | correlation 0.15, shap 0.10 | forecast 0.35, sensitivity 0.25, historical 0.15, correlation 0.10, causal 0.10, shap 0.05 |
| SHAP role | 10% signal | ≤5%, top-5 only, flag-first |
| Agreement | signal_agreement | **family_agreement** primary; model can't vote 3× |
| Plausibility | absent | **BusinessPlausibilityCheck** before verdict |
| Multi-KPI | Phase 2 | **MVP Phase 0** |
| Contradicted | proposed keep | **locked: always keep, rank lower** |
| Supported threshold | 2 signals | **2 families**, with empirical/historical backstop |

---

## One thing to confirm before implementation

**Family backstop rule** — I recommend:

> `supported` requires ≥2 agreeing families **and** at least one of `{historical, empirical}` agreeing.

Alternative (slightly looser): allow `supported` with model + historical only (correlation agrees, causal inconclusive), but **never** model + shap alone.

Which do you prefer?

- **A)** Model + empirical OR model + historical (recommended)  
- **B)** Model + historical counts even without experiments  
- **C)** Any 2 families, no backstop (looser, more false supported)

Once you pick A/B/C, the plan is locked and I'll implement MVP steps 1–8.

OPTION - B

Locked. **Option B** is now the adjudication rule for `supported`.

---

## Final adjudication rule (Option B)

**`supported` requires:**

1. **`families_agreeing ≥ 2`**
2. **At least one agreeing family is `historical` OR `empirical`** — but **`model + historical` alone is sufficient** (experiments not required)
3. **`model_based` family ≠ `contradict`**
4. **Primary KPI forecast `direction_match == true`** (or forecast is `negligible` → forecast inconclusive, not a veto)
5. **`plausibility != implausible`**

**Valid paths to `supported`:**

| Path | Example |
|------|---------|
| Model + historical | Forecast agrees + lag correlation agrees; no past experiments needed |
| Model + empirical | Forecast agrees + 3/4 past discount tests won |
| Historical + empirical | Rare but valid — strong correlation + experiment history, weak forecast |
| All three | Strongest case → `confidence_band: high` |

**Not sufficient alone:**

| Path | Result |
|------|--------|
| Model only (forecast + sensitivity + SHAP all agree) | `inconclusive` — model family counts as **one** vote, need a second family |
| Empirical only | `inconclusive` |
| Historical only (correlation agrees, causal inconclusive) | `inconclusive` unless a second family joins |

---

## Locked plan summary (v2.1)

| Item | Decision |
|------|----------|
| Weights | forecast 0.35, sensitivity 0.25, historical 0.15, causal 0.10, correlation 0.10, shap 0.05 |
| SHAP | Top 5 hypotheses only, flag-first, max 0.05 weight |
| Independence | `family_agreement` primary; model family = one vote (best of forecast/sensitivity/shap) |
| Supported threshold | 2 families, **B: model + historical OK without experiments** |
| Multi-KPI coherence | MVP, 5 drivers |
| Plausibility | Sanity layer before verdict |
| Contradicted | Always kept, ranked lower |
| Sensitivity | Extend `SensitivityEngine` with `target_metric` |

---

## MVP implementation scope (when you're ready)

1. Resolver + data hygiene  
2. Multi-KPI coherence (5 drivers)  
3. `SensitivityEngine(target_metric)` + per-flow cache  
4. Forecast via `ScenarioSimulator`  
5. Correlation (lag) + causal + experiments  
6. SHAP top-5 only  
7. `BusinessPlausibilityCheck`  
8. Adjudication with family logic (Option B)  
9. Wire `ConfidenceScorer`, `Ranker`, `RecommendationEngine` to `adjudication`  
10. Tests for family paths, coherence trade-offs, plausibility  
