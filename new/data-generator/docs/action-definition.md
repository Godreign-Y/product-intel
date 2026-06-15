---

# 02_action_definition.md

```markdown
# ACTION DEFINITION

## Purpose

Represents intentional business interventions.

Actions are event driven.

---

# Action Event

```json
{
  "event_date": "date",

  "feature": "string",

  "delta": "float",

  "duration_days": "int"
}
````

---

# Supported Features

## Pricing

```text
avg_selling_price
discount_pct
shipping_fee
```

---

## Inventory

```text
inventory_available
```

---

## Marketing

```text
marketing_spend
```

---

## Sales Channels

```text
amazon
website
nykaa
mobile_app
```

---

## Campaign Mix

```text
search
social
email
affiliate
```

---

## Acquisition Mix

```text
google
instagram
facebook
organic
referral
email
```

---

# Examples

Price Increase

```json
{
  "event_date": "2025-01-01",
  "feature": "avg_selling_price",
  "delta": 10,
  "duration_days": 365
}
```

Discount Increase

```json
{
  "event_date": "2025-02-01",
  "feature": "discount_pct",
  "delta": 15,
  "duration_days": 30
}
```

---

# Action Schedule

A trajectory can contain multiple action events.

```json
[
  {...},
  {...},
  {...}
]
```

````