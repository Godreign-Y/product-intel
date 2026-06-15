# ACTION SCHEDULE GENERATOR SPEC

## Purpose

Generate realistic intervention schedules.

These schedules are attached to anchor states and drive future trajectories.

---

# Core Principle

A schedule is a sequence of action events.

Example:

```json
[
  {
    "day": 0,
    "feature": "avg_selling_price",
    "delta_pct": 10
  },
  {
    "day": 30,
    "feature": "discount_pct",
    "delta_pct": 15
  }
]
```

---

# Action Event Structure

```json
{
  "event_id": "",

  "relative_day": 0,

  "feature": "",

  "delta_pct": 0,

  "duration_days": 0
}
```

---

# Supported Features

==================================================
PRICE
==================================================

avg_selling_price

Range:

```text
-40% to +40%
```

Step Size:

```text
5%
```

---

==================================================
DISCOUNT
==================================================

discount_pct

Range:

```text
-50% to +50%
```

Step Size:

```text
5%
```

---

==================================================
SHIPPING
==================================================

shipping_fee

Range:

```text
-50% to +100%
```

Step Size:

```text
5%
```

---

==================================================
INVENTORY
==================================================

inventory_available

Range:

```text
-80% to +300%
```

Step Size:

```text
10%
```

---

==================================================
MARKETING
==================================================

marketing_spend

Range:

```text
-80% to +300%
```

Step Size:

```text
10%
```

---

==================================================
SALES CHANNEL MIX
==================================================

amazon

website

nykaa

mobile_app

Allowed Shift:

```text
5%
10%
15%
20%
25%
30%
```

Example:

Amazon -> Website

```json
{
  "amazon": -20,
  "website": 20
}
```

---

==================================================
CAMPAIGN MIX
==================================================

search

social

email

affiliate

Allowed Shift:

```text
5%
10%
15%
20%
25%
30%
```

---

==================================================
ACQUISITION MIX
==================================================

google

instagram

facebook

organic

referral

email

Allowed Shift:

```text
5%
10%
15%
20%
25%
30%
```

---

# Schedule Complexity

==================================================
SIMPLE
==================================================

Action Count:

```text
1
```

Distribution:

```text
40%
```

Examples:

```text
Price +10%

Discount +20%

Marketing +30%
```

---

==================================================
MEDIUM
==================================================

Action Count:

```text
2-3
```

Distribution:

```text
35%
```

Example:

```text
Price +10%

Day 30

Discount +15%
```

---

==================================================
COMPLEX
==================================================

Action Count:

```text
4-6
```

Distribution:

```text
20%
```

Example:

```text
Marketing +50%

Day 20

Price -10%

Day 45

Website +15%
```

---

==================================================
STRESS
==================================================

Action Count:

```text
7-15
```

Distribution:

```text
5%
```

---

# Event Timing

Allowed Range:

```text
0 - 365 days
```

---

Distribution

More likely near start.

Recommended:

```text
Beta Distribution

alpha=2
beta=5
```

This produces:

```text
Many early actions

Some later actions
```

---

# Duration Rules

PRICE

```text
90 - 365 days
```

---

DISCOUNT

```text
7 - 90 days
```

---

SHIPPING

```text
30 - 365 days
```

---

MARKETING

```text
7 - 120 days
```

---

INVENTORY

```text
1 - 30 days
```

---

CHANNEL MIX

```text
30 - 365 days
```

---

CAMPAIGN MIX

```text
14 - 120 days
```

---

ACQUISITION MIX

```text
30 - 365 days
```

---

# Conflict Resolution

Not allowed:

```text
Price +20%

and

Price -20%

same day
```

---

Allowed:

```text
Price +20%

Day 0

Price -10%

Day 45
```

Net:

```text
+10%
```

---

# Schedule Templates

These are business strategies.

==================================================
GROWTH STRATEGY
==================================================

Bias Toward:

```text
Marketing Increase

Discount Increase

Website Growth
```

---

==================================================
PROFIT STRATEGY
==================================================

Bias Toward:

```text
Price Increase

Marketing Optimization

Website Share Increase
```

---

==================================================
CLEARANCE STRATEGY
==================================================

Bias Toward:

```text
Discount Increase

Inventory Reduction
```

---

==================================================
D2C STRATEGY
==================================================

Bias Toward:

```text
Amazon -> Website

Amazon -> Mobile App
```

---

# POC Generation Targets

Products:

```text
10
```

Anchors Per Product:

```text
12
```

Suggested:

```text
Day

30
60
90
120
150
180
210
240
270
300
330
360
```

---

Schedules Per Anchor:

```text
20
```

Breakdown:

```text
8 Simple

7 Medium

4 Complex

1 Stress
```

---

Total Schedules

```text
10 products

×

12 anchors

×

20 schedules

=

2400 schedules
```

---

# Final POC Trajectories

Baseline

```text
10
```

Branch Trajectories

```text
2400
```

Total

```text
2410
```

---

# Output Format

action_schedules.parquet

Schema:

```json
{
  "schedule_id": "",

  "product_id": "",

  "anchor_day": 0,

  "complexity": "",

  "events": []
}
```