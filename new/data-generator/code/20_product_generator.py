import json
import random
from dataclasses import dataclass, asdict

random.seed(42)

# =====================================================
# ARCHETYPE DEFINITIONS
# =====================================================

ARCHETYPES = {
    "Mass Market Beauty": {
        "category": "Beauty",
        "subcategory": "Skincare",
        "brand": "Brand_A",

        "price_range": (100, 500),
        "inventory_range": (2000, 10000),
        "traffic_range": (2000, 10000),
        "conversion_range": (0.02, 0.06),
        "retention_range": (0.20, 0.40),

        "price_sensitivity": 1.5,
        "discount_sensitivity": 1.5,
        "marketing_sensitivity": 1.0,
        "inventory_sensitivity": 1.0,

        "retention_multiplier": 1.0,
        "ltv_multiplier": 1.0,
        "seasonality_multiplier": 1.0
    },

    "Premium Beauty": {
        "category": "Beauty",
        "subcategory": "Skincare",
        "brand": "Brand_B",

        "price_range": (1000, 5000),
        "inventory_range": (200, 1500),
        "traffic_range": (500, 5000),
        "conversion_range": (0.01, 0.04),
        "retention_range": (0.30, 0.60),

        "price_sensitivity": 0.6,
        "discount_sensitivity": 0.8,
        "marketing_sensitivity": 1.4,
        "inventory_sensitivity": 0.8,

        "retention_multiplier": 1.3,
        "ltv_multiplier": 1.4,
        "seasonality_multiplier": 1.0
    },

    "Impulse Purchase": {
        "category": "Beauty",
        "subcategory": "Consumables",
        "brand": "Brand_C",

        "price_range": (50, 500),
        "inventory_range": (1000, 10000),
        "traffic_range": (5000, 50000),
        "conversion_range": (0.03, 0.12),
        "retention_range": (0.10, 0.30),

        "price_sensitivity": 1.2,
        "discount_sensitivity": 1.8,
        "marketing_sensitivity": 1.5,
        "inventory_sensitivity": 0.7,

        "retention_multiplier": 0.7,
        "ltv_multiplier": 0.7,
        "seasonality_multiplier": 0.8
    },

    "Research Driven": {
        "category": "Electronics",
        "subcategory": "Gadgets",
        "brand": "Brand_A",

        "price_range": (1000, 10000),
        "inventory_range": (500, 5000),
        "traffic_range": (1000, 10000),
        "conversion_range": (0.01, 0.03),
        "retention_range": (0.20, 0.50),

        "price_sensitivity": 1.0,
        "discount_sensitivity": 0.8,
        "marketing_sensitivity": 0.9,
        "inventory_sensitivity": 0.8,

        "retention_multiplier": 1.0,
        "ltv_multiplier": 1.1,
        "seasonality_multiplier": 0.9
    },

    "Premium Electronics": {
        "category": "Electronics",
        "subcategory": "Gadgets",
        "brand": "Brand_B",

        "price_range": (10000, 100000),
        "inventory_range": (50, 500),
        "traffic_range": (500, 5000),
        "conversion_range": (0.005, 0.02),
        "retention_range": (0.05, 0.20),

        "price_sensitivity": 1.2,
        "discount_sensitivity": 1.4,
        "marketing_sensitivity": 1.0,
        "inventory_sensitivity": 1.5,

        "retention_multiplier": 0.8,
        "ltv_multiplier": 1.1,
        "seasonality_multiplier": 1.5
    },

    "Commodity FMCG": {
        "category": "FMCG",
        "subcategory": "Consumables",
        "brand": "Brand_C",

        "price_range": (20, 300),
        "inventory_range": (5000, 50000),
        "traffic_range": (3000, 30000),
        "conversion_range": (0.04, 0.10),
        "retention_range": (0.40, 0.80),

        "price_sensitivity": 1.8,
        "discount_sensitivity": 1.6,
        "marketing_sensitivity": 0.6,
        "inventory_sensitivity": 1.2,

        "retention_multiplier": 1.4,
        "ltv_multiplier": 1.1,
        "seasonality_multiplier": 0.6
    },

    "Subscription Product": {
        "category": "Beauty",
        "subcategory": "Consumables",
        "brand": "Brand_A",

        "price_range": (100, 2000),
        "inventory_range": (0, 0),
        "traffic_range": (1000, 10000),
        "conversion_range": (0.02, 0.05),
        "retention_range": (0.60, 0.95),

        "price_sensitivity": 0.9,
        "discount_sensitivity": 0.5,
        "marketing_sensitivity": 1.0,
        "inventory_sensitivity": 0.0,

        "retention_multiplier": 2.0,
        "ltv_multiplier": 2.0,
        "seasonality_multiplier": 0.5
    },

    "Trend Product": {
        "category": "Beauty",
        "subcategory": "Consumables",
        "brand": "Brand_B",

        "price_range": (100, 3000),
        "inventory_range": (500, 5000),
        "traffic_range": (1000, 50000),
        "conversion_range": (0.01, 0.08),
        "retention_range": (0.05, 0.20),

        "price_sensitivity": 0.7,
        "discount_sensitivity": 1.0,
        "marketing_sensitivity": 2.0,
        "inventory_sensitivity": 0.7,

        "retention_multiplier": 0.6,
        "ltv_multiplier": 0.7,
        "seasonality_multiplier": 1.2
    },

    "Luxury Product": {
        "category": "Beauty",
        "subcategory": "Skincare",
        "brand": "Brand_C",

        "price_range": (5000, 100000),
        "inventory_range": (20, 200),
        "traffic_range": (100, 2000),
        "conversion_range": (0.005, 0.02),
        "retention_range": (0.20, 0.60),

        "price_sensitivity": 0.4,
        "discount_sensitivity": 0.4,
        "marketing_sensitivity": 1.5,
        "inventory_sensitivity": 0.6,

        "retention_multiplier": 1.2,
        "ltv_multiplier": 1.8,
        "seasonality_multiplier": 1.1
    },

    "Inventory Sensitive": {
        "category": "Electronics",
        "subcategory": "Gadgets",
        "brand": "Brand_A",

        "price_range": (500, 5000),
        "inventory_range": (100, 5000),
        "traffic_range": (1000, 15000),
        "conversion_range": (0.01, 0.05),
        "retention_range": (0.20, 0.50),

        "price_sensitivity": 1.0,
        "discount_sensitivity": 1.0,
        "marketing_sensitivity": 0.9,
        "inventory_sensitivity": 2.0,

        "retention_multiplier": 1.0,
        "ltv_multiplier": 1.0,
        "seasonality_multiplier": 1.0
    }
}


def rand_pct_mix(keys):
    vals = [random.random() for _ in keys]
    s = sum(vals)
    vals = [round(v / s * 100, 2) for v in vals]

    diff = round(100 - sum(vals), 2)
    vals[0] += diff

    return dict(zip(keys, vals))


def generate_product(product_id, archetype_name, cfg):

    price = round(random.uniform(*cfg["price_range"]), 2)
    inventory = random.randint(*cfg["inventory_range"])
    traffic = random.randint(*cfg["traffic_range"])

    conversion = round(random.uniform(*cfg["conversion_range"]), 4)
    retention = round(random.uniform(*cfg["retention_range"]), 4)

    orders = max(1, int(traffic * conversion))

    revenue = round(orders * price, 2)

    margin = round(
        random.uniform(0.2, 0.6),
        4
    )

    profit = round(
        revenue * margin,
        2   
    )


    with open("simulator/config/simulation_assumptions.json", "r") as f:
        assumptions = json.load(f)
    
    inventory_policy = assumptions["inventory_policies"].get(archetype_name, "weekly")

    return {
        "product_id": product_id,
        "archetype": archetype_name,
        "inventory_policy": inventory_policy,

        "category": cfg["category"],
        "subcategory": cfg["subcategory"],
        "brand": cfg["brand"],

        "base_state": {
            "inventory_available": inventory,

            "avg_selling_price": price,
            "discount_pct": 0,
            "shipping_fee": 0,

            "marketing_spend": round(revenue * 0.10, 2),

            "sales_channel_mix": rand_pct_mix(
                ["amazon", "website", "nykaa", "mobile_app"]
            ),

            "campaign_mix": rand_pct_mix(
                ["search", "social", "email", "affiliate"]
            ),

            "acquisition_mix": rand_pct_mix(
                [
                    "google",
                    "instagram",
                    "facebook",
                    "organic",
                    "referral",
                    "email"
                ]
            ),
            "margin": margin,
            "traffic": traffic,
            "active_users": int(traffic * 0.4),

            "current_ctr": round(random.uniform(0.01, 0.08), 4),

            "current_roas": round(random.uniform(1.5, 6), 2),

            "orders": orders,
            "revenue": revenue,
            "profit": profit,

            "conversion_rate": conversion,
            "retention_rate": retention,

            "avg_ltv": round(price * random.uniform(2, 8), 2)
        },

        "behavior_parameters": {
            k: v
            for k, v in cfg.items()
            if "sensitivity" in k
            or "multiplier" in k
        }
    }


def main():

    products = []

    for idx, (name, cfg) in enumerate(ARCHETYPES.items(), start=1):

        pid = f"P{idx:03}"

        products.append(
            generate_product(pid, name, cfg)
        )

    with open("products.json", "w") as f:
        json.dump(products, f, indent=2)

    print(f"Generated {len(products)} products")


if __name__ == "__main__":
    main()