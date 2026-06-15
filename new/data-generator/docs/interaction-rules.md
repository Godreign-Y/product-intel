# 05_interaction_rules.md

```markdown
# INTERACTION RULES

## Purpose

Defines nonlinear interactions between actions.

---

# Rule Structure

```json
{
  "action_a": "",

  "action_b": "",

  "interaction_type": "",

  "multiplier": 1.0
}
````

---

# Types

```text
synergy

cannibalization

saturation

suppression
```

---

# Example

Discount

*

Marketing

```json
{
  "action_a": "discount_pct",
  "action_b": "marketing_spend",

  "interaction_type": "synergy",

  "multiplier": 1.25
}
```

---

# Example

Marketing

*

Marketing

```json
{
  "action_a": "marketing_spend",
  "action_b": "marketing_spend",

  "interaction_type": "saturation",

  "multiplier": 0.75
}
```

````