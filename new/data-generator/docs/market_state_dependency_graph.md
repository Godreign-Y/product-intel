This is actually the graph that will drive the simulator.

Most people start with:

```text
Price -> Revenue
Marketing -> Orders
```

But that's wrong.

The simulator should mostly work through market-state propagation.

Meaning:

```text
Marketing
    ↓
Traffic
    ↓
Active Users
    ↓
Orders
    ↓
Revenue
    ↓
Profit
```

instead of directly modifying everything.

---

# 13_market_state_dependency_graph.md

## Purpose

Defines relationships between market state variables.

This graph executes after:

```text
Controllable State Effects
```

and before:

```text
Noise
Seasonality
Market Shocks
```

---

# Market State Variables

```text
traffic

active_users

ctr

roas

orders

revenue

profit

conversion_rate

retention_rate

avg_ltv
```

---

# Core Principle

The graph must be mostly acyclic.

Bad:

```text
Traffic
→ Orders

Orders
→ Traffic
```

---

Good:

```text
Traffic
→ Active Users
→ Orders
→ Revenue
→ Profit
```

---

# Layer 1

## Awareness Layer

---

### CTR → Traffic

Strength:

STRONG

Reason:

Better click performance drives visitors.

```text
CTR
→
Traffic
```

---

### Acquisition Quality → Traffic

Handled in Phase 1 graph.

Not repeated here.

---

# Layer 2

## Engagement Layer

---

### Traffic → Active Users

Strength:

DOMINANT

Reason:

Traffic creates active users.

```text
Traffic
→
Active Users
```

---

### Traffic → Orders

Strength:

WEAK

Reason:

Some visitors buy immediately.

```text
Traffic
→
Orders
```

---

# Layer 3

## Conversion Layer

---

### Active Users → Orders

Strength:

DOMINANT

Reason:

Most orders originate from active users.

```text
Active Users
→
Orders
```

---

### Conversion Rate → Orders

Strength:

DOMINANT

Reason:

Primary conversion equation.

```text
Conversion Rate
→
Orders
```

---

### Traffic → Orders

Strength:

MODERATE

Reason:

Conversion funnel.

```text
Traffic
→
Orders
```

---

# Layer 4

## Revenue Layer

---

### Orders → Revenue

Strength:

DOMINANT

Reason:

Revenue originates from orders.

```text
Orders
→
Revenue
```

---

### Avg Selling Price → Revenue

Handled by controllable graph.

Not repeated.

---

# Layer 5

## Profit Layer

---

### Revenue → Profit

Strength:

DOMINANT

Reason:

Profit originates from revenue.

```text
Revenue
→
Profit
```

---

### Orders → Profit

Strength:

MODERATE

Reason:

Order volume affects costs.

```text
Orders
→
Profit
```

---

### ROAS → Profit

Strength:

STRONG

Reason:

Marketing efficiency impacts profitability.

```text
ROAS
→
Profit
```

---

# Layer 6

## Retention Layer

---

### Active Users → Retention

Strength:

MODERATE

Reason:

Engagement drives retention.

```text
Active Users
→
Retention
```

---

### Orders → Retention

Strength:

STRONG

Reason:

Purchasing creates repeat behavior.

```text
Orders
→
Retention
```

---

# Layer 7

## Lifetime Value Layer

---

### Retention → LTV

Strength:

DOMINANT

Reason:

Primary LTV driver.

```text
Retention
→
LTV
```

---

### Orders → LTV

Strength:

STRONG

Reason:

Repeat purchases increase LTV.

```text
Orders
→
LTV
```

---

### Revenue → LTV

Strength:

MODERATE

Reason:

Higher spenders generate higher LTV.

```text
Revenue
→
LTV
```

---

# ROAS Dependencies

ROAS is special.

ROAS should not be treated as an independent KPI.

Instead:

```text
ROAS

=

Revenue Attributed To Marketing

/

Marketing Spend
```

---

Therefore:

### Revenue → ROAS

Strength:

STRONG

---

### Marketing Spend → ROAS

Handled in controllable graph.

---

# Graph Matrix

```text
Source                Target              Strength

CTR                   Traffic             STRONG

Traffic               Active Users        DOMINANT

Traffic               Orders              MODERATE

Active Users          Orders              DOMINANT

Conversion Rate       Orders              DOMINANT

Orders                Revenue             DOMINANT

Revenue               Profit              DOMINANT

Orders                Profit              MODERATE

ROAS                  Profit              STRONG

Active Users          Retention           MODERATE

Orders                Retention           STRONG

Retention             LTV                 DOMINANT

Orders                LTV                 STRONG

Revenue               LTV                 MODERATE

Revenue               ROAS                STRONG
```

---

# Very Important Realization

After creating this graph, many edges in the previous graph should become weaker.

Example:

Instead of:

```text
Marketing
→ Revenue
```

being strong,

we should have:

```text
Marketing
→ Traffic

Traffic
→ Active Users

Active Users
→ Orders

Orders
→ Revenue
```

This is much more realistic.

---