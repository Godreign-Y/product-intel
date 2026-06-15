# PRODUCT INSTANCE SPEC

## Purpose

Defines how products are generated from archetypes.

---

# Example

Archetype

Premium Beauty

↓

Generated Product

```json
{
  "product_id": "PB001",

  "category": "Beauty",

  "subcategory": "Skincare",

  "brand": "Brand_A",

  "base_price": 1500,

  "base_inventory": 500,

  "base_traffic": 2000,

  "base_conversion": 0.03,

  "base_retention": 0.45
}


Archetype Variability

Each product generated from an archetype receives random variation.

Example

Premium Beauty

Price Range

1500 ± 20%

Traffic Range

2000 ± 30%

Conversion Range

3% ± 25%

Retention Range

45% ± 15%