# 26_TRAINING_DATASET_SPECIFICATION.md

# Purpose

This document explains:

1. Why the training dataset was structured this way.
2. What the model is expected to learn.
3. How to train ML models on this dataset.
4. How to perform inference.
5. What NOT to do.

This document is the authoritative reference for all future model development.

---

# Original Business Objective

We want to answer questions such as:

```text
What happens if I increase price by 10%?

What happens if I increase discount by 20%?

What happens if I double marketing spend?

What happens if I shift traffic from Amazon to Website?

What happens if I combine multiple interventions?

What will the market state look like after N days?
```

Where:

```text
N can be any value.

1 day
7 days
14 days
57 days
123 days
365 days
```

The horizon is not fixed.

---

# Key Design Decision

We are NOT training a forecasting model.

We are training a dynamics model.

---

# Forecasting Model

Forecasting models learn:

```text
Current State

↓

State At Horizon H
```

Example:

```text
Today

↓

Day 90
```

Such models do not learn how the system evolves.

They only learn final outcomes.

---

# Dynamics Model

The chosen approach is:

```text
(state_t)

↓

(state_t+1)
```

The model learns:

```text
How the business evolves one day at a time.
```

This is equivalent to learning business physics.

---

# Why This Approach Was Chosen

Advantages:

```text
Supports arbitrary horizons.

Supports unseen intervention sequences.

Supports compound interventions.

Supports future simulation.

Supports trajectory generation.
```

Example:

```text
Day 0

↓

Day 1

↓

Day 2

↓

Day 3

...

↓

Day 365
```

The model can generate the entire trajectory.

---

# Dataset Structure

Each row represents:

```text
One State Transition
```

Meaning:

```text
state_t

↓

state_t+1
```

---

# Metadata Columns

These columns are for debugging only.

Do NOT use them as model inputs.

```text
trajectory_id
schedule_id
product_id
day
```

Purpose:

```text
Traceability

Debugging

Validation
```

---

# Input Features

These columns describe the current business state.

---

## Controllable Variables

```text
inventory_available

avg_selling_price

effective_price

discount_pct

shipping_fee

marketing_spend
```

These are business decisions.

---

## Market Variables

```text
traffic

active_users

current_ctr

current_roas

orders

fulfilled_orders

revenue

profit

conversion_rate

retention_rate

avg_ltv
```

These describe market response.

---

## Sales Channel Mix

```text
sales_mix_amazon

sales_mix_website

sales_mix_nykaa

sales_mix_mobile_app
```

---

## Campaign Mix

```text
campaign_mix_search

campaign_mix_social

campaign_mix_email

campaign_mix_affiliate
```

---

## Acquisition Mix

```text
acq_mix_google

acq_mix_instagram

acq_mix_facebook

acq_mix_organic

acq_mix_referral

acq_mix_email
```

---

# Intervention Metadata

These columns describe active intervention state.

Example:

```text
Price increase started 10 days ago.

Discount started 20 days ago.
```

---

Columns:

```text
price_age

discount_age

shipping_fee_age

marketing_spend_age

inventory_available_age

sales_channel_mix_age

campaign_mix_age

acquisition_mix_age
```

Meaning:

```text
-1

means

No active intervention
```

Example:

```text
discount_age = 15

means

Current discount intervention
started 15 days ago.
```

Purpose:

```text
Allows model to learn lag / peak / decay behavior.
```

---

# Target Variables

The model predicts:

```text
next_traffic

next_active_users

next_orders

next_revenue

next_profit

next_conversion_rate

next_retention_rate

next_avg_ltv
```

These represent:

```text
state_t+1
```

---

# Important Modeling Principle

The model predicts:

```text
Market State
```

The model does NOT predict:

```text
Price

Discount

Marketing Spend

Inventory

Mixes
```

Reason:

These are known control inputs.

They are supplied by the user.

They should not be forecasted.

---

# What The Model Learns

The model learns:

```text
Business Dynamics
```

Examples:

```text
Marketing

↓

Traffic

↓

Orders

↓

Revenue
```

```text
Discount

↓

Conversion

↓

Orders
```

```text
Retention

↓

LTV
```

The model learns these relationships from simulator-generated trajectories.

---

# How Inference Works

Assume current state:

```text
Day 0
```

User requests:

```text
Price +10%

Marketing +50%

Forecast 180 Days
```

---

Step 1

Apply intervention.

Construct:

```text
state_0
```

---

Step 2

Predict:

```text
state_1
```

---

Step 3

Feed prediction back.

Predict:

```text
state_2
```

---

Repeat:

```text
180 times
```

---

Final result:

```text
state_180
```

---

Trajectory:

```text
state_1

state_2

state_3

...

state_180
```

is also available.

---

# Why Horizon Is Not A Feature

We intentionally do NOT train:

```text
(state, horizon)

↓

future_state
```

Reason:

The model should learn business dynamics.

Not memorize horizon-specific patterns.

The horizon naturally emerges through repeated rollouts.

---

# LightGBM / XGBoost Training

Recommended first benchmark.

---

## Inputs

Use:

```text
All State Features

+

All Mix Features

+

All Age Features
```

Exclude:

```text
trajectory_id

schedule_id

product_id

day
```

---

## Targets

Train one model per target.

Example:

```text
Model 1

traffic → next_traffic
```

```text
Model 2

orders → next_orders
```

etc.

---

Total:

```text
8 models
```

Recommended.

---

# Why Separate Models

Advantages:

```text
Simpler

Easier debugging

Feature importance available

Fast training
```

---

# TFT Training

Future deep-learning benchmark.

---

Inputs:

```text
Full feature vector
```

Targets:

```text
All target variables simultaneously
```

---

Advantages:

```text
Multi-output

Temporal representation

Learned embeddings
```

---

# Mix Features Future Plan

Current implementation:

```text
Flattened Columns
```

Example:

```text
sales_mix_amazon

sales_mix_website
```

This is for POC simplicity.

---

Future implementation:

```text
Embedding Based Representation
```

Example:

```text
Amazon

Website

Nykaa

Mobile App
```

become learned vectors.

This supports:

```text
New Channels

Removed Channels

Schema Changes
```

without retraining feature definitions.

---

# Validation Before Training

Always verify:

```text
No NaNs

No Negative Orders

No Negative Revenue

Mixes Sum To 100

Targets Present
```

---

# Validation After Training

Always evaluate:

```text
MAE

RMSE

SMAPE
```

for every target.

---

# Most Important Evaluation

Evaluate intervention accuracy.

Example:

```text
Price +10%

Actual Revenue Change = -8%

Predicted Revenue Change = -7%
```

This metric matters more than raw RMSE.

---

# What NOT To Do

Do NOT:

```text
Use trajectory_id as feature.

Use schedule_id as feature.

Use product_id as feature.

Predict controllable variables.

Predict fixed horizons directly.

Shuffle away validation chronology.
```

---

# Long-Term Goal

The trained model should act as a learned business simulator.

Input:

```text
Current State

+

Intervention Plan
```

Output:

```text
Future Trajectory
```

for any horizon requested by the user.
