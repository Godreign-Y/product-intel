# PRODUCT GENERATOR SPEC

## Purpose

Generate realistic product instances from archetypes.

Output:

One product definition JSON.

Example:

```json
{
  "product_id": "P001",

  "archetype": "Premium Beauty",

  "category": "Beauty",

  "subcategory": "Skincare",

  "brand": "Brand_A",

  "base_state": {
    ...
  }
}
```

---

# POC Scope

Number Of Products

10

One product per archetype.

```text
P001 -> Mass Market Beauty

P002 -> Premium Beauty

P003 -> Impulse Purchase

P004 -> Research Driven

P005 -> Premium Electronics

P006 -> Commodity FMCG

P007 -> Subscription Product

P008 -> Trend Product

P009 -> Luxury Product

P010 -> Inventory Sensitive
```

---

# Product Structure

Every product contains:

```json
{
  "metadata": {},

  "baseline_parameters": {},

  "behavior_parameters": {}
}
```

---

==================================================
METADATA
==================================================

```json
{
  "product_id": "",

  "archetype": "",

  "category": "",

  "subcategory": "",

  "brand": ""
}
```

---

POC Categories

```text
Beauty
Electronics
FMCG
```

---

POC Subcategories

```text
Skincare
Gadgets
Consumables
```

---

POC Brands

```text
Brand_A
Brand_B
Brand_C
```

---

==================================================
BASELINE PARAMETERS
==================================================

These define starting business characteristics.

```json
{
  "base_price": 0,

  "base_inventory": 0,

  "base_marketing_spend": 0,

  "base_traffic": 0,

  "base_active_users": 0,

  "base_ctr": 0,

  "base_conversion_rate": 0,

  "base_retention_rate": 0,

  "base_ltv": 0
}
```

---

==================================================
BEHAVIOR PARAMETERS
==================================================

These define how the product reacts.

```json
{
  "price_sensitivity": 0,

  "discount_sensitivity": 0,

  "marketing_sensitivity": 0,

  "inventory_sensitivity": 0,

  "retention_multiplier": 0,

  "ltv_multiplier": 0,

  "seasonality_multiplier": 0
}
```

Loaded directly from:

```text
11_archetype_overrides.md
```

---

# Parameter Ranges

==================================================
Mass Market Beauty
==================================================

Price

100 - 500

Inventory

2000 - 10000

Traffic

2000 - 10000

Conversion

2% - 6%

Retention

20% - 40%

---

==================================================
Premium Beauty
==================================================

Price

1000 - 5000

Inventory

200 - 1500

Traffic

500 - 5000

Conversion

1% - 4%

Retention

30% - 60%

---

==================================================
Impulse Purchase
==================================================

Price

50 - 500

Inventory

1000 - 10000

Traffic

5000 - 50000

Conversion

3% - 12%

Retention

10% - 30%

---

==================================================
Research Driven
==================================================

Price

1000 - 10000

Inventory

500 - 5000

Traffic

1000 - 10000

Conversion

1% - 3%

Retention

20% - 50%

---

==================================================
Premium Electronics
==================================================

Price

10000 - 100000

Inventory

50 - 500

Traffic

500 - 5000

Conversion

0.5% - 2%

Retention

5% - 20%

---

==================================================
Commodity FMCG
==================================================

Price

20 - 300

Inventory

5000 - 50000

Traffic

3000 - 30000

Conversion

4% - 10%

Retention

40% - 80%

---

==================================================
Subscription Product
==================================================

Price

100 - 2000

Inventory

0

Traffic

1000 - 10000

Conversion

2% - 5%

Retention

60% - 95%

---

==================================================
Trend Product
==================================================

Price

100 - 3000

Inventory

500 - 5000

Traffic

1000 - 50000

Conversion

1% - 8%

Retention

5% - 20%

---

==================================================
Luxury Product
==================================================

Price

5000 - 100000

Inventory

20 - 200

Traffic

100 - 2000

Conversion

0.5% - 2%

Retention

20% - 60%

---

==================================================
Inventory Sensitive
==================================================

Price

500 - 5000

Inventory

100 - 5000

Traffic

1000 - 15000

Conversion

1% - 5%

Retention

20% - 50%

---

# Derived Initial Metrics

Generated automatically.

Orders

```text
orders

=

traffic × conversion_rate
```

Revenue

```text
revenue

=

orders × price
```

Profit

```text
profit

=

revenue × margin
```

Margin

Random

```text
20% - 60%
```

ROAS

Random

```text
1.5 - 6
```

---

# Initial Mixes

Sales Channel Mix

```json
{
  "amazon": x,
  "website": x,
  "nykaa": x,
  "mobile_app": x
}
```

Must sum to:

```text
100%
```

---

Campaign Mix

```json
{
  "search": x,
  "social": x,
  "email": x,
  "affiliate": x
}
```

Must sum to:

```text
100%
```

---

Acquisition Mix

```json
{
  "google": x,
  "instagram": x,
  "facebook": x,
  "organic": x,
  "referral": x,
  "email": x
}
```

Must sum to:

```text
100%
```

---

# Output File

products.json

Example

```json
[
  {
    "product_id": "P001",
    ...
  }
]
```

---

# Validation Rules

Price > 0

Traffic > 0

Conversion < 1

Retention < 1

Mixes Sum To 100

Inventory >= 0

LTV > Price