## Section A

### Data Quality Validation

Run checks:

```python
inventory_available >= 0

traffic >= 0

active_users >= 0

orders >= 0

revenue >= 0

avg_selling_price > 0

discount_pct >= 0

discount_pct <= 100

conversion_rate >= 0
conversion_rate <= 1

retention_rate >= 0
retention_rate <= 1

current_ctr >= 0
current_ctr <= 1

avg_ltv > 0
```

---

Expected:

```text
0 violations
```

---

## Section B

### Mix Validation

For every row:

```python
sum(sales_channel_mix.values()) == 100

sum(campaign_mix.values()) == 100

sum(acquisition_mix.values()) == 100
```

Tolerance:

```python
±0.01
```

---

Expected:

```text
100%
```

---

## Section C

### Inventory Validation

Check:

```python
inventory(t+1)

=

inventory(t)

-
fulfilled_orders

+
restock
```

---

Validate:

```text
No negative inventory
```

---

Validate:

```text
Stockouts happen
```

for some trajectories.

---

## Section D

### Derived Metrics Validation

Verify:

```python
effective_price

=

avg_selling_price
*
(1-discount_pct/100)
```

---

Verify:

```python
revenue

≈

orders
*
effective_price
```

---

Verify:

```python
profit

≈

revenue
*
margin
```

---

Verify:

```python
roas

≈

revenue
/
marketing_spend
```

---

# Section E

### Elasticity Validation

This is huge.

---

Find trajectories containing:

```text
Price Increase
```

---

Measure:

```python
Before

After
```

for:

```text
conversion
orders
revenue
profit
```

---

Expected:

```text
conversion ↓

orders ↓
```

---

Repeat for:

```text
Discount Increase

Marketing Increase

Inventory Increase

Website Share Increase
```

---

# Section F

### Market Graph Validation

This is the most important.

Verify:

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

actually exists.

---

Statistical check:

```python
corr(
traffic,
active_users
)
```

Expected:

```text
Strong Positive
```

---

Likewise:

```text
active_users ↔ orders

orders ↔ revenue

revenue ↔ profit

retention ↔ ltv
```

---

Expected:

```text
positive relationships
```

---

# Section G

### Lag Validation

Find:

```text
Marketing Increase
```

---

Verify:

```text
Immediate effect = small

Peak effect ≈ day 14

Decay afterwards
```

---

Same for:

```text
Price

Discount

Channel Mix
```

---

This validates:

```text
15_lag_peak_decay_library.md
```

---

# Section H

### Archetype Validation

Example:

```text
Luxury Product
```

Should show:

```text
Low price sensitivity
```

---

Compare:

```text
Luxury

vs

Commodity FMCG
```

under:

```text
Price +10%
```

---

Expected:

```text
Luxury affected less
```

---

# Section I

### Compound Intervention Validation

Example trajectory:

```text
Day 0

Price +10%

Day 30

Discount +20%

Day 60

Marketing +50%
```

---

Check:

```text
Simulator remains stable.
```

---

No:

```text
negative revenue

negative traffic

exploding values
```