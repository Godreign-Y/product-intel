# LAG PEAK DECAY LIBRARY

## Purpose

Defines how effects evolve through time.

Every edge in the causal graph references one of these profiles.

---

# Terminology

Lag

Days before effect starts.

Peak

Days until maximum effect.

Decay

Days until effect mostly disappears.

---

# Effect Types

1. Immediate
2. Fast
3. Medium
4. Slow
5. Long-Term
6. Structural

---

==================================================
PROFILE A
IMMEDIATE
==================================================

Description:

Effect starts immediately.

Used For:

Inventory
Stockouts

```json
{
  "lag_days": 0,
  "peak_days": 1,
  "decay_days": 3
}
```

Curve

```text
Day

0   100%
1   100%
2   60%
3   20%
```

---

==================================================
PROFILE B
FAST RESPONSE
==================================================

Description:

Customer notices quickly.

Used For:

Price

Discount

Shipping Fee

```json
{
  "lag_days": 1,
  "peak_days": 5,
  "decay_days": 30
}
```

Curve

```text
0   0%

1   20%

2   50%

3   75%

5   100%

10  80%

20  50%

30  20%
```

---

==================================================
PROFILE C
MARKETING RESPONSE
==================================================

Description:

Awareness takes time.

Used For:

Marketing Spend

Campaign Mix

```json
{
  "lag_days": 2,
  "peak_days": 14,
  "decay_days": 60
}
```

Curve

```text
0   0%

2   10%

5   30%

10  70%

14  100%

21  90%

30  70%

45  40%

60  15%
```

---

==================================================
PROFILE D
CHANNEL RESPONSE
==================================================

Description:

Users adapt gradually.

Used For:

Sales Channel Mix

```json
{
  "lag_days": 5,
  "peak_days": 21,
  "decay_days": 90
}
```

Curve

```text
0   0%

5   10%

10  30%

15  60%

21  100%

30  95%

60  70%

90  30%
```

---

==================================================
PROFILE E
ACQUISITION RESPONSE
==================================================

Description:

Traffic quality changes slowly.

Used For:

Acquisition Mix

```json
{
  "lag_days": 7,
  "peak_days": 30,
  "decay_days": 120
}
```

Curve

```text
0    0%

7    10%

14   30%

21   60%

30   100%

45   95%

60   80%

90   50%

120  20%
```

---

==================================================
PROFILE F
RETENTION RESPONSE
==================================================

Description:

Customer loyalty changes very slowly.

Used For:

Retention

LTV

```json
{
  "lag_days": 14,
  "peak_days": 60,
  "decay_days": 180
}
```

Curve

```text
0     0%

14    5%

30    20%

45    50%

60    100%

90    90%

120   70%

180   30%
```

---

==================================================
PROFILE G
SEASONAL RESPONSE
==================================================

Description:

Recurring seasonal effects.

Used For:

Holiday Effects

Seasonality

```json
{
  "lag_days": 0,
  "peak_days": 0,
  "decay_days": 365
}
```

---

# Edge Mapping

PRICE

Price → *

PROFILE_B

---

DISCOUNT

Discount → *

PROFILE_B

---

SHIPPING

Shipping → *

PROFILE_B

---

INVENTORY

Inventory → *

PROFILE_A

---

MARKETING

Marketing → *

PROFILE_C

---

SALES CHANNEL

Channel Mix → *

PROFILE_D

---

ACQUISITION

Acquisition Mix → *

PROFILE_E

---

RETENTION

Retention → LTV

PROFILE_F

---

SEASONALITY

Seasonality

PROFILE_G

---

# Archetype Overrides

Final Profile

=

Base Profile

×

Archetype Multipliers

Example

Trend Product

```json
{
  "lag_multiplier": 0.7,

  "peak_multiplier": 0.8,

  "decay_multiplier": 1.2
}
```

Meaning:

Faster reaction

Higher peak

Longer persistence

---

# Simulator Equation

Effect Strength

=

Elasticity

×

Curve Value

×

Archetype Multiplier

×

Interaction Multiplier

×

Noise Multiplier