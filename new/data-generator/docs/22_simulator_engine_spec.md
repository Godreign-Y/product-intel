# SIMULATOR ENGINE SPEC

## Purpose

Generate future business trajectories.

Input:

1. Product
2. Anchor State
3. Action Schedule
4. Number Of Days

Output:

Future State Trajectory

---

# High Level

Simulator executes:

Current State

↓

Apply Active Actions

↓

Apply Effect Curves

↓

Apply Market Propagation

↓

Apply Interactions

↓

Apply Seasonality

↓

Apply Noise

↓

Generate Next State

↓

Repeat

---

# Inputs

==================================================
PRODUCT
==================================================

Product Instance

Generated from:

20_product_generator.py

Contains:

- Metadata
- Baseline Parameters
- Archetype Parameters

---

==================================================
ANCHOR STATE
==================================================

State at day t

Contains:

Controllable State

+

Market State

---

==================================================
ACTION SCHEDULE
==================================================

Generated from:

21_action_schedule_generator.py

Contains:

Action Events

---

==================================================
SIMULATION LENGTH
==================================================

Default

365 Days

---

# State Structure

Current State

```python
{
    "inventory_available": ...,

    "avg_selling_price": ...,
    "discount_pct": ...,
    "shipping_fee": ...,

    "marketing_spend": ...,

    "sales_channel_mix": {...},

    "campaign_mix": {...},

    "acquisition_mix": {...},

    "traffic": ...,
    "active_users": ...,

    "current_ctr": ...,
    "current_roas": ...,

    "orders": ...,
    "revenue": ...,
    "profit": ...,

    "conversion_rate": ...,
    "retention_rate": ...,

    "avg_ltv": ...
}
```

---

# Simulation Loop

For each day:

```python
for day in simulation_days:
```

Execute:

```text
1 Active Actions

2 Effect Curves

3 Direct Effects

4 Market Propagation

5 Interactions

6 Seasonality

7 Noise

8 Constraints

9 Save State
```

---

# Step 1

Active Actions

Determine:

Which events are currently active.

Example

Price +10%

Day 0

Duration 180

At Day 45

Still Active

---

Output

```python
active_actions
```

---

# Step 2

Effect Curves

For every active action:

Compute:

```text
Lag

Peak

Decay
```

using

15_lag_peak_decay_library.md

---

Output

```python
curve_multiplier
```

Example

```text
Day 5

0.85
```

---

# Step 3

Direct Effects

Apply:

```text
Elasticity

×

Curve

×

Archetype Multiplier
```

Formula

```python
effect = (
    elasticity
    *
    curve_value
    *
    archetype_multiplier
)
```

---

Example

```text
Price +10%

Elasticity

-0.8

Curve

0.75

Archetype

1.5
```

Produces

```text
Conversion

-9%
```

---

Output

```python
updated_market_state
```

---

# Step 4

Market Propagation

Apply graph:

13_market_state_dependency_graph.md

---

Example

```text
Traffic ↑

↓

Active Users ↑

↓

Orders ↑

↓

Revenue ↑

↓

Profit ↑
```

---

Apply sequentially.

---

Output

```python
propagated_state
```

---

# Step 5

Interaction Engine

Apply:

05_interaction_rules.md

---

Examples

```text
Price

+

Discount
```

---

```text
Marketing

+

Discount
```

---

```text
Marketing

+

Marketing
```

---

Output

```python
interaction_adjusted_state
```

---

# Step 6

Seasonality

Apply:

Weekly

Monthly

Quarterly

Yearly

Patterns

---

Example

Holiday Spike

```text
Traffic +20%
```

---

Output

```python
seasonal_state
```

---

# Step 7

Noise

Apply:

Random Gaussian Noise

---

Suggested

```python
traffic

σ = 3%
```

---

```python
orders

σ = 2%
```

---

```python
revenue

σ = 2%
```

---

Purpose

Prevent deterministic world.

---

# Step 8

Constraints

Ensure:

---

Traffic

```text
>= 0
```

---

Orders

```text
>= 0
```

---

Revenue

```text
>= 0
```

---

Profit

```text
can be negative
```

---

Conversion

```text
0 - 1
```

---

Retention

```text
0 - 1
```

---

Mixes

```text
Sum = 100
```

---

Inventory

```text
>= 0
```

---

# Step 9

Store State

Append

```python
state_t
```

to trajectory.

---

# Output

Trajectory

```python
[
    state_day_1,
    state_day_2,
    ...
    state_day_365
]
```

---

# Trajectory Schema

Columns

```text
trajectory_id

product_id

day

all_state_variables

active_actions
```

---

# POC Simplifications

For V1

DO NOT IMPLEMENT

- Competitor Simulation
- Economic Conditions
- RL Planning
- Optimizer
- Explainability Engine

Only:

- Direct Effects
- Propagation
- Interactions
- Seasonality
- Noise

---

# Success Criteria

Given:

Current State

+

Action Schedule

Simulator produces:

365-day trajectory

with

- realistic lag
- realistic peak
- realistic decay
- archetype behavior
- interaction effects