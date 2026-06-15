# ARCHETYPE OVERRIDES

## Purpose

Defines how each archetype modifies the global causal graph.

The simulator first loads:

1. Base Causal Graph
2. Archetype Overrides

Final Effect:

Final Elasticity
=
Base Elasticity × Archetype Multiplier

---

# Multiplier Scale

0.25 = Very Weak

0.50 = Weak

0.75 = Reduced

1.00 = Default

1.25 = Elevated

1.50 = Strong

2.00 = Very Strong

---

# Archetype 1

Mass Market Beauty

## Description

Price-sensitive products with frequent purchases.

```json
{
  "price_sensitivity": 1.50,
  "discount_sensitivity": 1.50,
  "marketing_sensitivity": 1.00,
  "inventory_sensitivity": 1.00,

  "retention_multiplier": 1.00,
  "ltv_multiplier": 1.00,

  "seasonality_multiplier": 1.00
}
```

---

# Archetype 2

Premium Beauty

## Description

Brand-driven premium products.

```json
{
  "price_sensitivity": 0.60,
  "discount_sensitivity": 0.80,
  "marketing_sensitivity": 1.40,
  "inventory_sensitivity": 0.80,

  "retention_multiplier": 1.30,
  "ltv_multiplier": 1.40,

  "seasonality_multiplier": 1.00
}
```

---

# Archetype 3

Impulse Purchase

## Description

Fast decision purchases.

```json
{
  "price_sensitivity": 1.20,
  "discount_sensitivity": 1.80,
  "marketing_sensitivity": 1.50,
  "inventory_sensitivity": 0.70,

  "retention_multiplier": 0.70,
  "ltv_multiplier": 0.70,

  "seasonality_multiplier": 0.80
}
```

---

# Archetype 4

Research Driven Product

## Description

Users compare extensively before buying.

```json
{
  "price_sensitivity": 1.00,
  "discount_sensitivity": 0.80,
  "marketing_sensitivity": 0.90,
  "inventory_sensitivity": 0.80,

  "retention_multiplier": 1.00,
  "ltv_multiplier": 1.10,

  "seasonality_multiplier": 0.90
}
```

---

# Archetype 5

Premium Electronics

## Description

High-ticket products.

```json
{
  "price_sensitivity": 1.20,
  "discount_sensitivity": 1.40,
  "marketing_sensitivity": 1.00,
  "inventory_sensitivity": 1.50,

  "retention_multiplier": 0.80,
  "ltv_multiplier": 1.10,

  "seasonality_multiplier": 1.50
}
```

---

# Archetype 6

Commodity FMCG

## Description

Frequent low-value purchases.

```json
{
  "price_sensitivity": 1.80,
  "discount_sensitivity": 1.60,
  "marketing_sensitivity": 0.60,
  "inventory_sensitivity": 1.20,

  "retention_multiplier": 1.40,
  "ltv_multiplier": 1.10,

  "seasonality_multiplier": 0.60
}
```

---

# Archetype 7

Subscription Product

## Description

Recurring purchase behavior.

```json
{
  "price_sensitivity": 0.90,
  "discount_sensitivity": 0.50,
  "marketing_sensitivity": 1.00,
  "inventory_sensitivity": 0.00,

  "retention_multiplier": 2.00,
  "ltv_multiplier": 2.00,

  "seasonality_multiplier": 0.50
}
```

---

# Archetype 8

Trend Driven Product

## Description

Demand driven by attention.

```json
{
  "price_sensitivity": 0.70,
  "discount_sensitivity": 1.00,
  "marketing_sensitivity": 2.00,
  "inventory_sensitivity": 0.70,

  "retention_multiplier": 0.60,
  "ltv_multiplier": 0.70,

  "seasonality_multiplier": 1.20
}
```

---

# Archetype 9

Luxury Product

## Description

Prestige-driven demand.

```json
{
  "price_sensitivity": 0.40,
  "discount_sensitivity": 0.40,
  "marketing_sensitivity": 1.50,
  "inventory_sensitivity": 0.60,

  "retention_multiplier": 1.20,
  "ltv_multiplier": 1.80,

  "seasonality_multiplier": 1.10
}
```

---

# Archetype 10

Inventory Sensitive Product

## Description

Sales highly dependent on availability.

```json
{
  "price_sensitivity": 1.00,
  "discount_sensitivity": 1.00,
  "marketing_sensitivity": 0.90,
  "inventory_sensitivity": 2.00,

  "retention_multiplier": 1.00,
  "ltv_multiplier": 1.00,

  "seasonality_multiplier": 1.00
}
```

---

# POC Product Mapping

For POC generation:

```text
P001 -> Mass Market Beauty
P002 -> Premium Beauty
P003 -> Impulse Purchase
P004 -> Research Driven
P005 -> Premium Electronics
P006 -> Commodity FMCG
P007 -> Subscription Product
P008 -> Trend Driven Product
P009 -> Luxury Product
P010 -> Inventory Sensitive Product
```

---

# Future Extension

New archetypes can be added by defining:

1. New archetype name
2. Sensitivity multipliers
3. Channel preferences
4. Acquisition preferences
5. Seasonality behavior

No changes required in:

- Causal Graph
- Simulator Engine
- Dataset Generator
- Model Training Pipeline