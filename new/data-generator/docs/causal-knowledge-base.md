# 04_causal_knowledge_base.md

```markdown
# CAUSAL KNOWLEDGE BASE

## Purpose

Defines relationships between controllable variables and market variables.

---

# Relationship Structure

```json
{
  "source": "",
  "target": "",

  "direction": "",

  "strength": 0.0,

  "lag_days": 0,

  "peak_days": 0,

  "decay_days": 0
}
````

---

# Example

avg_selling_price

→

conversion_rate

```json
{
  "source": "avg_selling_price",
  "target": "conversion_rate",

  "direction": "negative",

  "strength": 0.7,

  "lag_days": 1,

  "peak_days": 5,

  "decay_days": 45
}
```

---

# Strength Scale

```text
0.0 - no effect

0.1 - very weak

0.3 - weak

0.5 - moderate

0.7 - strong

0.9 - dominant
```

````


# Controllable Variable 1

## avg_selling_price

---

### Traffic

YES

Reason:

Higher prices discourage browsing and clicks.

Strength:

Moderate

---

### Active Users

YES

Reason:

Fewer visitors become active.

Strength:

Weak

---

### CTR

YES

Reason:

Expensive products reduce ad attractiveness.

Strength:

Weak

---

### ROAS

YES

Reason:

Higher prices increase revenue per sale.

Strength:

Moderate

---

### Orders

YES

Reason:

Price elasticity.

Strength:

Strong

---

### Revenue

YES

Reason:

Direct price component.

Strength:

Strong

---

### Profit

YES

Reason:

Margin expansion.

Strength:

Strong

---

### Conversion

YES

Reason:

Primary effect.

Strength:

Very Strong

---

### Retention

WEAK

Reason:

Customer satisfaction/value perception.

Strength:

Weak

---

### LTV

WEAK

Reason:

Retention effect chain.

Strength:

Weak

---

# Price Summary

```text
Traffic          ✓
Active Users     ✓
CTR              ✓
ROAS             ✓
Orders           ✓
Revenue          ✓
Profit           ✓
Conversion       ✓
Retention        (weak)
LTV              (weak)
```

---

# Controllable Variable 2

## discount_pct

---

Traffic

✓

---

Active Users

✓

---

CTR

✓

---

ROAS

✗

Actually often negative.

---

Orders

✓

---

Revenue

✓

---

Profit

✓ negative

---

Conversion

✓

---

Retention

✓

Discount-driven customers can repeat.

---

LTV

✓

---

# Discount Summary

```text
Traffic          ✓
Active Users     ✓
CTR              ✓
ROAS             ✓
Orders           ✓
Revenue          ✓
Profit           ✓
Conversion       ✓
Retention        ✓
LTV              ✓
```

---

# Controllable Variable 3

## shipping_fee

---

Traffic

✓

---

Active Users

✓

---

CTR

✗

People don't know shipping fee before clicking.

---

ROAS

✗

Indirect.

---

Orders

✓

---

Revenue

✓

---

Profit

✓

---

Conversion

✓

---

Retention

✓ weak

---

LTV

✓ weak

---

# Shipping Summary

```text
Traffic          ✓
Active Users     ✓
CTR              ✗
ROAS             ✗
Orders           ✓
Revenue          ✓
Profit           ✓
Conversion       ✓
Retention        (weak)
LTV              (weak)
```

---

# Controllable Variable 4

## inventory_available

---

Traffic

✗

---

Active Users

✗

---

CTR

✗

---

ROAS

✗

---

Orders

✓

---

Revenue

✓

---

Profit

✓

---

Conversion

✓

---

Retention

✓

---

LTV

✓

---

# Inventory Summary

```text
Traffic          ✗
Active Users     ✗
CTR              ✗
ROAS             ✗
Orders           ✓
Revenue          ✓
Profit           ✓
Conversion       ✓
Retention        ✓
LTV              ✓
```

---

# Controllable Variable 5

## marketing_spend

This is the strongest variable.

---

Traffic

✓

---

Active Users

✓

---

CTR

✓

---

ROAS

✓

---

Orders

✓

---

Revenue

✓

---

Profit

✓

---

Conversion

✓

---

Retention

✓

---

LTV

✓

---

# Marketing Summary

```text
Everything ✓
```

---

# Controllable Variable 6

## sales_channel_mix

(Amazon / Website / Mobile)

---

Traffic

✓

---

Active Users

✓

---

CTR

✗

---

ROAS

✓

---

Orders

✓

---

Revenue

✓

---

Profit

✓

---

Conversion

✓

---

Retention

✓

---

LTV

✓

---

# Controllable Variable 7

## campaign_mix

(Search/Social/Email/Affiliate)

---

Traffic

✓

---

Active Users

✓

---

CTR

✓

---

ROAS

✓

---

Orders

✓

---

Revenue

✓

---

Profit

✓

---

Conversion

✓

---

Retention

✓

---

LTV

✓

---

# Controllable Variable 8

## acquisition_mix

(Google/Organic/Facebook/etc)

---

Traffic

✓

---

Active Users

✓

---

CTR

✓

---

ROAS

✓

---

Orders

✓

---

Revenue

✓

---

Profit

✓

---

Conversion

✓

---

Retention

✓

---

LTV

✓

---

# Final Edge Count

Possible:

```text
80
```

---

Meaningful direct edges:

```text
~55-60
```

---

Weak/Indirect:

```text
~10
```

---

Should not exist:

```text
~10-15
```

---

For the simulator, I would classify every edge into:

```text
NONE
WEAK
MODERATE
STRONG
DOMINANT
```
