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