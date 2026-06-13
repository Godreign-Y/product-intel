import json

import numpy as np
import pandas as pd
from faker import Faker


# DATA GENERATION CONFIGURATION
num_products = 100
start_date = "2025-01-01"
end_date = "2025-12-31"
experiments_per_family = 50
random_seed = 42


rng = np.random.default_rng(random_seed)
fake = Faker("en_IN")
Faker.seed(random_seed)

OUTPUT_TEMPORAL = "temporal_dataset.csv"
OUTPUT_EXPERIMENT = "experiment_dataset.csv"
OUTPUT_DICTIONARY = "data_dictionary.csv"

DATE_START = pd.Timestamp(start_date)
DATE_END = pd.Timestamp(end_date)
DATES = pd.date_range(DATE_START, DATE_END, freq="D")
NUM_DAYS = len(DATES)

CATEGORIES = {
    "Skincare": "Serum",
    "Haircare": "Shampoo",
    "Makeup": "Lipstick",
}
BRANDS = ["Minimalist", "Mamaearth", "The Derma Co"]
AGE_GROUPS = ["18-24", "25-34", "35-44", "45+"]

SALES_CHANNEL_KEYS = ["Amazon", "Website", "Nykaa", "MobileApp"]
CAMPAIGN_KEYS = ["Search", "Social", "Email", "Affiliate"]
ACQUISITION_KEYS = ["Google", "Instagram", "Facebook", "Email", "Organic", "Referral"]

SALES_FLAT = {
    "Amazon": "amazon_sales_pct",
    "Website": "website_sales_pct",
    "Nykaa": "nykaa_sales_pct",
    "MobileApp": "mobile_app_sales_pct",
}
CAMPAIGN_FLAT = {
    "Search": "search_campaign_pct",
    "Social": "social_campaign_pct",
    "Email": "email_campaign_pct",
    "Affiliate": "affiliate_campaign_pct",
}
ACQUISITION_FLAT = {
    "Google": "google_source_pct",
    "Instagram": "instagram_source_pct",
    "Facebook": "facebook_source_pct",
    "Email": "email_source_pct",
    "Organic": "organic_source_pct",
    "Referral": "referral_source_pct",
}

TEMPORAL_COLUMNS = [
    "date",
    "product_id",
    "category",
    "subcategory",
    "brand",
    "avg_ltv",
    "dominant_age_group",
    "inventory_available",
    "avg_selling_price",
    "discount_pct",
    "shipping_fee",
    "sales_channel_mix",
    "campaign_mix",
    "acquisition_mix",
    "amazon_sales_pct",
    "website_sales_pct",
    "nykaa_sales_pct",
    "mobile_app_sales_pct",
    "search_campaign_pct",
    "social_campaign_pct",
    "email_campaign_pct",
    "affiliate_campaign_pct",
    "google_source_pct",
    "instagram_source_pct",
    "facebook_source_pct",
    "email_source_pct",
    "organic_source_pct",
    "referral_source_pct",
    "marketing_spend",
    "traffic",
    "active_users",
    "current_ctr",
    "current_roas",
    "orders",
    "revenue",
    "profit",
    "conversion_rate",
    "retention_rate",
]

EXPERIMENT_TYPES = [
    "Price Increase",
    "Price Decrease",
    "Discount Increase",
    "Discount Decrease",
    "Shipping Fee Increase",
    "Shipping Fee Decrease",
    "Free Shipping",
    "Marketing Spend Increase",
    "Marketing Spend Decrease",
    "Inventory Increase",
    "Inventory Reduction",
    "Amazon to Website Shift",
    "Website to Amazon Shift",
    "Amazon to Mobile App Shift",
    "Website to Mobile App Shift",
    "Channel Mix Optimization",
    "Search Increase",
    "Social Increase",
    "Email Increase",
    "Affiliate Increase",
    "Campaign Mix Optimization",
    "Google to Instagram Shift",
    "Instagram to Google Shift",
    "Facebook to Google Shift",
    "Paid to Organic Shift",
    "Acquisition Mix Optimization",
    "Premium Pricing Strategy",
    "Aggressive Growth Strategy",
    "Profit Optimization Strategy",
    "Conversion Recovery Strategy",
    "Inventory Clearance Strategy",
    "D2C Growth Strategy",
]


def round_money(value):
    return float(np.round(value, 2))


def normalize_mix(mix):
    """Normalize any current or future mix keys to sum to exactly 100."""
    clean = {str(k): max(float(v), 0.0) for k, v in mix.items()}
    total = sum(clean.values())
    if total <= 0:
        equal = 100.0 / max(len(clean), 1)
        clean = {k: equal for k in clean} if clean else {"Unknown": 100.0}
    else:
        clean = {k: v * 100.0 / total for k, v in clean.items()}

    rounded = {k: round(v, 2) for k, v in clean.items()}
    drift = round(100.0 - sum(rounded.values()), 2)
    largest_key = max(rounded, key=rounded.get)
    rounded[largest_key] = round(rounded[largest_key] + drift, 2)
    return rounded


def make_mix(keys, weights, concentration):
    values = rng.dirichlet(np.array(weights) * concentration)
    return normalize_mix(dict(zip(keys, values * 100.0)))


def move_mix_share(mix, source_key, target_key, points):
    updated = dict(mix)
    updated.setdefault(source_key, 0.0)
    updated.setdefault(target_key, 0.0)
    movable = min(float(points), max(updated[source_key] - 3.0, 0.0))
    updated[source_key] -= movable
    updated[target_key] += movable
    return normalize_mix(updated)


def apply_mix_plan(mix, moves):
    updated = dict(mix)
    for source_key, target_key, points in moves:
        updated = move_mix_share(updated, source_key, target_key, points)
    return normalize_mix(updated)


def json_dumps(value):
    return json.dumps(value, sort_keys=True)


def product_price(category, brand):
    category_range = {
        "Skincare": (520, 1190),
        "Haircare": (280, 760),
        "Makeup": (260, 950),
    }[category]
    brand_multiplier = {"Minimalist": 1.10, "Mamaearth": 0.88, "The Derma Co": 1.03}[brand]
    raw_price = rng.uniform(*category_range) * brand_multiplier
    return int(np.round(raw_price / 10.0) * 10)


def create_products(n_products):
    products = []
    category_cycle = list(CATEGORIES.items())
    brand_cycle = BRANDS

    for idx in range(1, n_products + 1):
        category, subcategory = category_cycle[(idx - 1) % len(category_cycle)]
        brand = brand_cycle[(idx + rng.integers(0, 3)) % len(brand_cycle)]
        price = product_price(category, brand)
        unit_cost_ratio = {
            "Skincare": rng.uniform(0.28, 0.42),
            "Haircare": rng.uniform(0.34, 0.48),
            "Makeup": rng.uniform(0.25, 0.39),
        }[category]
        base_demand = {
            "Skincare": rng.uniform(95, 185),
            "Haircare": rng.uniform(80, 160),
            "Makeup": rng.uniform(70, 150),
        }[category] * {"Minimalist": 1.04, "Mamaearth": 1.12, "The Derma Co": 0.98}[brand]
        base_spend = base_demand * rng.uniform(32, 58)
        base_inventory = int(base_demand * rng.uniform(6.0, 12.0))
        dominant_age = rng.choice(
            AGE_GROUPS,
            p={
                "Skincare": [0.18, 0.49, 0.24, 0.09],
                "Haircare": [0.14, 0.43, 0.29, 0.14],
                "Makeup": [0.35, 0.42, 0.17, 0.06],
            }[category],
        )
        product_id = f"P{idx:03d}"
        descriptor = fake.word().title()

        products.append(
            {
                "product_id": product_id,
                "product_name": f"{brand} {descriptor} {subcategory}",
                "category": category,
                "subcategory": subcategory,
                "brand": brand,
                "base_price": price,
                "unit_cost": round_money(price * unit_cost_ratio),
                "base_demand": base_demand,
                "base_spend": base_spend,
                "base_inventory": base_inventory,
                "base_discount": {
                    "Skincare": rng.uniform(8, 16),
                    "Haircare": rng.uniform(10, 20),
                    "Makeup": rng.uniform(12, 24),
                }[category],
                "base_shipping_fee": 0 if price >= 899 and rng.random() < 0.45 else rng.choice([39, 49, 59, 69]),
                "base_conversion": {
                    "Skincare": rng.uniform(0.030, 0.055),
                    "Haircare": rng.uniform(0.026, 0.048),
                    "Makeup": rng.uniform(0.023, 0.045),
                }[category],
                "base_ctr": {
                    "Skincare": rng.uniform(0.018, 0.034),
                    "Haircare": rng.uniform(0.015, 0.030),
                    "Makeup": rng.uniform(0.020, 0.040),
                }[category],
                "base_retention": {
                    "Skincare": rng.uniform(0.36, 0.55),
                    "Haircare": rng.uniform(0.30, 0.48),
                    "Makeup": rng.uniform(0.22, 0.38),
                }[category],
                "dominant_age_group": dominant_age,
                "sales_channel_mix": make_mix(
                    SALES_CHANNEL_KEYS,
                    {
                        "Minimalist": [0.32, 0.39, 0.18, 0.11],
                        "Mamaearth": [0.44, 0.24, 0.21, 0.11],
                        "The Derma Co": [0.30, 0.34, 0.24, 0.12],
                    }[brand],
                    concentration=32,
                ),
                "campaign_mix": make_mix(
                    CAMPAIGN_KEYS,
                    {
                        "Skincare": [0.43, 0.29, 0.18, 0.10],
                        "Haircare": [0.36, 0.31, 0.19, 0.14],
                        "Makeup": [0.27, 0.46, 0.15, 0.12],
                    }[category],
                    concentration=35,
                ),
                "acquisition_mix": make_mix(
                    ACQUISITION_KEYS,
                    {
                        "Skincare": [0.44, 0.21, 0.10, 0.08, 0.13, 0.04],
                        "Haircare": [0.38, 0.18, 0.14, 0.09, 0.16, 0.05],
                        "Makeup": [0.28, 0.34, 0.14, 0.07, 0.12, 0.05],
                    }[category],
                    concentration=40,
                ),
                "phase": rng.uniform(0, 2 * np.pi),
            }
        )

    return pd.DataFrame(products)


def festival_multiplier(date, category):
    year = date.year
    windows = [
        (pd.Timestamp(year=year, month=3, day=10), pd.Timestamp(year=year, month=3, day=16), {"Skincare": 1.08, "Haircare": 1.06, "Makeup": 1.24}),
        (pd.Timestamp(year=year, month=5, day=6), pd.Timestamp(year=year, month=5, day=12), {"Skincare": 1.16, "Haircare": 1.13, "Makeup": 1.18}),
        (pd.Timestamp(year=year, month=8, day=13), pd.Timestamp(year=year, month=8, day=17), {"Skincare": 1.18, "Haircare": 1.15, "Makeup": 1.20}),
        (pd.Timestamp(year=year, month=10, day=10), pd.Timestamp(year=year, month=10, day=27), {"Skincare": 1.28, "Haircare": 1.20, "Makeup": 1.42}),
        (pd.Timestamp(year=year, month=11, day=24), pd.Timestamp(year=year, month=11, day=30), {"Skincare": 1.24, "Haircare": 1.21, "Makeup": 1.26}),
        (pd.Timestamp(year=year, month=12, day=22), pd.Timestamp(year=year, month=12, day=31), {"Skincare": 1.16, "Haircare": 1.09, "Makeup": 1.31}),
    ]
    multiplier = 1.0
    for start, end, effect in windows:
        if start <= date <= end:
            multiplier *= effect[category]
    return multiplier


def seasonal_multiplier(date, category, phase):
    day_of_year = date.dayofyear
    week_factor = 1.08 if date.dayofweek in [5, 6] else 0.98
    month_factor = 1.0 + 0.05 * np.sin(2 * np.pi * day_of_year / 30.4 + phase)
    quarter_factor = {1: 0.96, 2: 1.03, 3: 1.05, 4: 1.14}[date.quarter]

    category_factor = 1.0
    if category == "Skincare":
        if date.month in [4, 5, 6]:
            category_factor *= 1.11
        if date.month in [11, 12, 1]:
            category_factor *= 1.09
    elif category == "Haircare":
        if date.month in [6, 7, 8, 9]:
            category_factor *= 1.16
    elif category == "Makeup":
        if date.month in [10, 11, 12]:
            category_factor *= 1.18

    return week_factor * month_factor * quarter_factor * category_factor * festival_multiplier(date, category)


def build_temporal_baseline(products):
    rows = []
    brand_trend = {"Minimalist": 0.18, "Mamaearth": 0.09, "The Derma Co": 0.15}

    for product in products.to_dict("records"):
        for date in DATES:
            progress = (date - DATE_START).days / max(NUM_DAYS - 1, 1)
            demand_factor = seasonal_multiplier(date, product["category"], product["phase"])
            trend_factor = 1.0 + brand_trend[product["brand"]] * progress
            sale_period = festival_multiplier(date, product["category"]) > 1.05
            monthly_sale = date.day <= 5 or date.day >= 27
            discount = product["base_discount"] + (5.0 if sale_period else 0.0) + (2.5 if monthly_sale else 0.0)
            discount += rng.normal(0, 1.2)
            discount = float(np.clip(discount, 0, 42))

            spend_noise = rng.lognormal(mean=0.0, sigma=0.12)
            marketing_spend = product["base_spend"] * demand_factor * trend_factor * spend_noise
            if sale_period:
                marketing_spend *= rng.uniform(1.10, 1.35)

            inventory_wave = 1.0 + 0.22 * np.sin(2 * np.pi * date.dayofyear / 28 + product["phase"])
            inventory_available = product["base_inventory"] * inventory_wave
            inventory_available += product["base_demand"] * rng.uniform(1.0, 3.2) if date.day in [1, 15] else 0
            inventory_available = int(max(12, inventory_available * rng.uniform(0.90, 1.10)))

            rows.append(
                {
                    "date": date,
                    "product_id": product["product_id"],
                    "category": product["category"],
                    "subcategory": product["subcategory"],
                    "brand": product["brand"],
                    "dominant_age_group": product["dominant_age_group"],
                    "inventory_available": inventory_available,
                    "avg_selling_price": float(product["base_price"]),
                    "discount_pct": round(discount, 2),
                    "shipping_fee": float(product["base_shipping_fee"]),
                    "sales_channel_mix": dict(product["sales_channel_mix"]),
                    "campaign_mix": dict(product["campaign_mix"]),
                    "acquisition_mix": dict(product["acquisition_mix"]),
                    "marketing_spend": round_money(marketing_spend),
                    "_demand_factor": demand_factor,
                    "_trend_factor": trend_factor,
                    "_base_demand": product["base_demand"],
                    "_base_spend": product["base_spend"],
                    "_unit_cost": product["unit_cost"],
                    "_base_conversion": product["base_conversion"],
                    "_base_ctr": product["base_ctr"],
                    "_base_retention": product["base_retention"],
                    "_base_price": product["base_price"],
                    "_base_ltv": product["base_price"] * rng.uniform(2.1, 4.6),
                }
            )

    return pd.DataFrame(rows)


def scalar_change(old, new):
    change_pct = 0.0 if old == 0 else ((new - old) / old) * 100.0
    return {"old": round(float(old), 2), "new": round(float(new), 2), "change_pct": round(float(change_pct), 2)}


def mix_changed_features(old_mix, new_mix, keys):
    changes = {}
    for key in keys:
        old = float(old_mix.get(key, 0.0))
        new = float(new_mix.get(key, 0.0))
        if abs(new - old) >= 0.01:
            changes[key] = {"old": round(old, 2), "new": round(new, 2), "change_pct": round(new - old, 2)}
    return changes


def interval_overlaps(existing_windows, start_value, end_value):
    return any(start_value <= existing_end and end_value >= existing_start for existing_start, existing_end in existing_windows)


def choose_experiment_dates(product_id, occupied_windows):
    if NUM_DAYS < 7:
        raise ValueError("Configured date range must contain at least 7 days for experiments.")

    max_duration = min(45, NUM_DAYS)
    compact_duration_max = min(14, max_duration)

    for attempt in range(800):
        if attempt < 300:
            duration = int(rng.integers(7, max_duration + 1))
        else:
            duration = int(rng.integers(7, compact_duration_max + 1))

        start_offset = int(rng.integers(0, NUM_DAYS - duration + 1))
        end_offset = start_offset + duration - 1
        if not interval_overlaps(occupied_windows[product_id], start_offset, end_offset):
            occupied_windows[product_id].append((start_offset, end_offset))
            start_value = DATE_START + pd.Timedelta(days=start_offset)
            end_value = DATE_START + pd.Timedelta(days=end_offset)
            return start_value, end_value

    return None, None


def build_experiment_plan(exp_type, start_row):
    old_price = float(start_row["avg_selling_price"])
    old_discount = float(start_row["discount_pct"])
    old_shipping = float(start_row["shipping_fee"])
    old_spend = float(start_row["marketing_spend"])
    old_inventory = float(start_row["inventory_available"])
    sales_mix = dict(start_row["sales_channel_mix"])
    campaign_mix = dict(start_row["campaign_mix"])
    acquisition_mix = dict(start_row["acquisition_mix"])

    scalar_updates = {}
    mix_updates = {}
    changed_features = {}
    primary_metric = "orders"
    expected_direction = "Increase"
    notes = ""

    def set_scalar(column, new_value):
        scalar_updates[column] = float(new_value)
        changed_features[column] = scalar_change(float(start_row[column]), float(new_value))

    def set_mix(column, old_mix, moves):
        new_mix = apply_mix_plan(old_mix, moves)
        mix_updates[column] = new_mix
        changed_features[column] = mix_changed_features(old_mix, new_mix, set(old_mix) | set(new_mix))

    if exp_type == "Price Increase":
        set_scalar("avg_selling_price", old_price * rng.uniform(1.08, 1.15))
        primary_metric, expected_direction = "profit", "Increase"
        notes = "Premium price test expects higher unit margin with some demand elasticity."
    elif exp_type == "Price Decrease":
        set_scalar("avg_selling_price", old_price * rng.uniform(0.86, 0.94))
        primary_metric, expected_direction = "orders", "Increase"
        notes = "Lower price should improve demand and conversion."
    elif exp_type == "Discount Increase":
        set_scalar("discount_pct", min(old_discount + rng.uniform(6, 14), 55))
        primary_metric, expected_direction = "orders", "Increase"
        notes = "Higher discount should lift orders but may dilute margin."
    elif exp_type == "Discount Decrease":
        set_scalar("discount_pct", max(old_discount - rng.uniform(4, 10), 0))
        primary_metric, expected_direction = "profit", "Increase"
        notes = "Lower discount tests whether stronger margin offsets order loss."
    elif exp_type == "Shipping Fee Increase":
        set_scalar("shipping_fee", old_shipping + rng.choice([20, 30, 40]))
        primary_metric, expected_direction = "conversion_rate", "Decrease"
        notes = "Higher shipping fee should create checkout friction."
    elif exp_type == "Shipping Fee Decrease":
        set_scalar("shipping_fee", max(old_shipping - rng.choice([20, 30, 40]), 0))
        primary_metric, expected_direction = "conversion_rate", "Increase"
        notes = "Reduced shipping fee should reduce checkout friction."
    elif exp_type == "Free Shipping":
        set_scalar("shipping_fee", 0)
        primary_metric, expected_direction = "conversion_rate", "Increase"
        notes = "Free shipping test should increase conversion and order volume."
    elif exp_type == "Marketing Spend Increase":
        set_scalar("marketing_spend", old_spend * rng.uniform(1.25, 1.65))
        primary_metric, expected_direction = "traffic", "Increase"
        notes = "Higher spend should increase traffic through paid reach and lagged adstock."
    elif exp_type == "Marketing Spend Decrease":
        set_scalar("marketing_spend", old_spend * rng.uniform(0.55, 0.78))
        primary_metric, expected_direction = "current_roas", "Increase"
        notes = "Spend reduction tests whether inefficient paid traffic can be trimmed."
    elif exp_type == "Inventory Increase":
        set_scalar("inventory_available", old_inventory * rng.uniform(1.30, 1.80))
        primary_metric, expected_direction = "orders", "Increase"
        notes = "Higher stock availability should reduce sales capacity constraints."
    elif exp_type == "Inventory Reduction":
        set_scalar("inventory_available", old_inventory * rng.uniform(0.35, 0.70))
        primary_metric, expected_direction = "revenue", "Decrease"
        notes = "Lower inventory should cap orders and revenue."
    elif exp_type == "Amazon to Website Shift":
        set_mix("sales_channel_mix", sales_mix, [("Amazon", "Website", rng.uniform(8, 16))])
        primary_metric, expected_direction = "website_sales_pct", "Increase"
        notes = "Channel share shifted from marketplace to owned website."
    elif exp_type == "Website to Amazon Shift":
        set_mix("sales_channel_mix", sales_mix, [("Website", "Amazon", rng.uniform(8, 16))])
        primary_metric, expected_direction = "amazon_sales_pct", "Increase"
        notes = "Channel share shifted toward Amazon for demand capture."
    elif exp_type == "Amazon to Mobile App Shift":
        set_mix("sales_channel_mix", sales_mix, [("Amazon", "MobileApp", rng.uniform(6, 14))])
        primary_metric, expected_direction = "mobile_app_sales_pct", "Increase"
        notes = "Marketplace users redirected toward app purchase journeys."
    elif exp_type == "Website to Mobile App Shift":
        set_mix("sales_channel_mix", sales_mix, [("Website", "MobileApp", rng.uniform(6, 14))])
        primary_metric, expected_direction = "mobile_app_sales_pct", "Increase"
        notes = "Owned web traffic nudged toward app conversion."
    elif exp_type == "Channel Mix Optimization":
        set_mix("sales_channel_mix", sales_mix, [("Amazon", "Website", 5), ("Nykaa", "MobileApp", 4)])
        primary_metric, expected_direction = "current_roas", "Increase"
        notes = "Mix optimized toward higher-margin owned channels."
    elif exp_type == "Search Increase":
        set_mix("campaign_mix", campaign_mix, [("Social", "Search", rng.uniform(6, 13))])
        primary_metric, expected_direction = "search_campaign_pct", "Increase"
        notes = "Search share increased for higher purchase intent."
    elif exp_type == "Social Increase":
        set_mix("campaign_mix", campaign_mix, [("Search", "Social", rng.uniform(6, 13))])
        primary_metric, expected_direction = "social_campaign_pct", "Increase"
        notes = "Social share increased for discovery and mid-funnel reach."
    elif exp_type == "Email Increase":
        set_mix("campaign_mix", campaign_mix, [("Social", "Email", rng.uniform(5, 11))])
        primary_metric, expected_direction = "retention_rate", "Increase"
        notes = "Email share increased to reactivate known buyers."
    elif exp_type == "Affiliate Increase":
        set_mix("campaign_mix", campaign_mix, [("Search", "Affiliate", rng.uniform(5, 11))])
        primary_metric, expected_direction = "affiliate_campaign_pct", "Increase"
        notes = "Affiliate share increased for deal-led acquisition."
    elif exp_type == "Campaign Mix Optimization":
        set_mix("campaign_mix", campaign_mix, [("Social", "Search", 4), ("Affiliate", "Email", 3)])
        primary_metric, expected_direction = "current_ctr", "Increase"
        notes = "Campaign mix optimized toward intent and lifecycle channels."
    elif exp_type == "Google to Instagram Shift":
        set_mix("acquisition_mix", acquisition_mix, [("Google", "Instagram", rng.uniform(6, 13))])
        primary_metric, expected_direction = "instagram_source_pct", "Increase"
        notes = "Acquisition shifted from search-led to creator and social discovery."
    elif exp_type == "Instagram to Google Shift":
        set_mix("acquisition_mix", acquisition_mix, [("Instagram", "Google", rng.uniform(6, 13))])
        primary_metric, expected_direction = "google_source_pct", "Increase"
        notes = "Acquisition shifted toward high-intent Google traffic."
    elif exp_type == "Facebook to Google Shift":
        set_mix("acquisition_mix", acquisition_mix, [("Facebook", "Google", rng.uniform(5, 11))])
        primary_metric, expected_direction = "google_source_pct", "Increase"
        notes = "Budget moved from Facebook to Google for better intent quality."
    elif exp_type == "Paid to Organic Shift":
        set_mix("acquisition_mix", acquisition_mix, [("Google", "Organic", 4), ("Instagram", "Organic", 4)])
        set_scalar("marketing_spend", old_spend * rng.uniform(0.72, 0.88))
        primary_metric, expected_direction = "organic_source_pct", "Increase"
        notes = "Paid dependency reduced while organic share is lifted."
    elif exp_type == "Acquisition Mix Optimization":
        set_mix("acquisition_mix", acquisition_mix, [("Facebook", "Google", 3), ("Referral", "Organic", 2)])
        primary_metric, expected_direction = "conversion_rate", "Increase"
        notes = "Acquisition mix optimized toward higher-converting sources."
    elif exp_type == "Premium Pricing Strategy":
        set_scalar("avg_selling_price", old_price * rng.uniform(1.08, 1.16))
        set_scalar("discount_pct", max(old_discount - rng.uniform(3, 8), 0))
        primary_metric, expected_direction = "profit", "Increase"
        notes = "Premium posture combines higher price with lower promotion depth."
    elif exp_type == "Aggressive Growth Strategy":
        set_scalar("marketing_spend", old_spend * rng.uniform(1.35, 1.85))
        set_scalar("discount_pct", min(old_discount + rng.uniform(6, 12), 55))
        set_scalar("shipping_fee", max(old_shipping - rng.choice([20, 30, 40]), 0))
        primary_metric, expected_direction = "orders", "Increase"
        notes = "Growth strategy combines paid reach, promotion, and reduced friction."
    elif exp_type == "Profit Optimization Strategy":
        set_scalar("discount_pct", max(old_discount - rng.uniform(4, 9), 0))
        set_scalar("marketing_spend", old_spend * rng.uniform(0.78, 0.92))
        set_mix("sales_channel_mix", sales_mix, [("Amazon", "Website", 4), ("Nykaa", "MobileApp", 3)])
        primary_metric, expected_direction = "profit", "Increase"
        notes = "Profit optimization trims inefficient spend and marketplace dependency."
    elif exp_type == "Conversion Recovery Strategy":
        set_scalar("shipping_fee", max(old_shipping - rng.choice([20, 30, 40]), 0))
        set_scalar("discount_pct", min(old_discount + rng.uniform(3, 8), 45))
        set_mix("campaign_mix", campaign_mix, [("Social", "Search", 3), ("Affiliate", "Email", 3)])
        primary_metric, expected_direction = "conversion_rate", "Increase"
        notes = "Conversion recovery lowers checkout friction and raises intent messaging."
    elif exp_type == "Inventory Clearance Strategy":
        set_scalar("discount_pct", min(old_discount + rng.uniform(10, 18), 60))
        set_scalar("avg_selling_price", old_price * rng.uniform(0.90, 0.97))
        primary_metric, expected_direction = "orders", "Increase"
        notes = "Clearance strategy accelerates sell-through using price and discount."
    elif exp_type == "D2C Growth Strategy":
        set_mix("sales_channel_mix", sales_mix, [("Amazon", "Website", 5), ("Nykaa", "MobileApp", 5)])
        set_scalar("marketing_spend", old_spend * rng.uniform(1.12, 1.35))
        primary_metric, expected_direction = "website_sales_pct", "Increase"
        notes = "D2C growth moves share toward owned web and app channels."

    return scalar_updates, mix_updates, changed_features, primary_metric, expected_direction, notes


def create_experiments(df, products, n_per_family):
    experiments = []
    product_ids = products["product_id"].tolist()
    occupied_windows = {product_id: [] for product_id in product_ids}

    exp_idx = 1
    for round_idx in range(n_per_family):
        for family_idx, exp_type in enumerate(EXPERIMENT_TYPES):
            candidate_ids = list(rng.permutation(product_ids))
            if exp_type in ["Free Shipping", "Shipping Fee Decrease"]:
                candidate_ids = [
                    product_id
                    for product_id in candidate_ids
                    if float(products.loc[products["product_id"] == product_id, "base_shipping_fee"].iloc[0]) > 0
                ]

            product_id = None
            start_date = None
            end_date = None
            for candidate_id in candidate_ids:
                candidate_start, candidate_end = choose_experiment_dates(candidate_id, occupied_windows)
                if candidate_start is not None:
                    product_id = candidate_id
                    start_date = candidate_start
                    end_date = candidate_end
                    break

            if product_id is None:
                raise ValueError(
                    "Unable to schedule all experiments without product-level overlap. "
                    "Reduce experiments_per_family, increase num_products, or extend the date range."
                )

            product = products.loc[products["product_id"] == product_id].iloc[0]
            start_row = df.loc[(df["product_id"] == product_id) & (df["date"] == start_date)].iloc[0]
            scalar_updates, mix_updates, changed_features, primary_metric, expected_direction, notes = build_experiment_plan(
                exp_type, start_row
            )

            experiments.append(
                {
                    "experiment_id": f"EXP{exp_idx:04d}",
                    "product_id": product_id,
                    "category": product["category"],
                    "subcategory": product["subcategory"],
                    "brand": product["brand"],
                    "experiment_type": exp_type,
                    "start_date": start_date,
                    "end_date": end_date,
                    "changed_features": changed_features,
                    "primary_metric": primary_metric,
                    "expected_direction": expected_direction,
                    "observed_effect_pct": np.nan,
                    "result": "Pending",
                    "confidence": np.nan,
                    "notes": notes,
                    "_scalar_updates": scalar_updates,
                    "_mix_updates": mix_updates,
                }
            )
            exp_idx += 1

    return pd.DataFrame(experiments)


def apply_experiments(df, experiments):
    df = df.copy()
    for column in ["inventory_available", "avg_selling_price", "discount_pct", "shipping_fee", "marketing_spend"]:
        df[column] = df[column].astype(float)
    for exp in experiments.to_dict("records"):
        mask = (
            (df["product_id"] == exp["product_id"])
            & (df["date"] >= exp["start_date"])
            & (df["date"] <= exp["end_date"])
        )
        for column, value in exp["_scalar_updates"].items():
            df.loc[mask, column] = value
        for column, mix in exp["_mix_updates"].items():
            df.loc[mask, column] = pd.Series([dict(mix) for _ in range(int(mask.sum()))], index=df.loc[mask].index)
    return df


def flatten_mix_columns(df):
    df = df.copy()
    for key, column in SALES_FLAT.items():
        df[column] = df["sales_channel_mix"].map(lambda x: round(float(x.get(key, 0.0)), 2))
    for key, column in CAMPAIGN_FLAT.items():
        df[column] = df["campaign_mix"].map(lambda x: round(float(x.get(key, 0.0)), 2))
    for key, column in ACQUISITION_FLAT.items():
        df[column] = df["acquisition_mix"].map(lambda x: round(float(x.get(key, 0.0)), 2))
    return df


def recompute_metrics(df):
    df = flatten_mix_columns(df).sort_values(["product_id", "date"]).copy()
    metric_rows = []

    for _, product_df in df.groupby("product_id", sort=False):
        lagged_spend = product_df["_base_spend"].iloc[0]
        lagged_orders = product_df["_base_demand"].iloc[0] * product_df["_base_conversion"].iloc[0] * 0.30

        for row in product_df.to_dict("records"):
            price = float(row["avg_selling_price"])
            discount = float(row["discount_pct"])
            net_price = price * (1.0 - discount / 100.0)
            shipping_fee = float(row["shipping_fee"])
            inventory = float(row["inventory_available"])
            spend = float(row["marketing_spend"])

            lagged_spend = 0.58 * lagged_spend + 0.42 * spend
            spend_index = lagged_spend / max(float(row["_base_spend"]), 1.0)
            price_index = price / max(float(row["_base_price"]), 1.0)
            price_elasticity = {
                "Skincare": -0.85,
                "Haircare": -1.05,
                "Makeup": -1.15,
            }[row["category"]]
            price_effect = np.clip(price_index ** price_elasticity, 0.55, 1.45)
            discount_effect = np.clip(1.0 + (discount - 12.0) * 0.018, 0.72, 1.65)
            shipping_effect = np.clip(1.0 - shipping_fee / max(price, 1.0) * 0.92, 0.68, 1.08)

            channel_reach = (
                row["amazon_sales_pct"] * 1.04
                + row["website_sales_pct"] * 0.94
                + row["nykaa_sales_pct"] * 0.98
                + row["mobile_app_sales_pct"] * 0.90
            ) / 100.0
            channel_conversion = (
                row["amazon_sales_pct"] * 0.94
                + row["website_sales_pct"] * 1.06
                + row["nykaa_sales_pct"] * 1.00
                + row["mobile_app_sales_pct"] * 1.13
            ) / 100.0
            channel_margin = (
                row["amazon_sales_pct"] * 0.82
                + row["website_sales_pct"] * 1.00
                + row["nykaa_sales_pct"] * 0.86
                + row["mobile_app_sales_pct"] * 1.03
            ) / 100.0

            campaign_ctr = (
                row["search_campaign_pct"] * 1.16
                + row["social_campaign_pct"] * 0.95
                + row["email_campaign_pct"] * 1.05
                + row["affiliate_campaign_pct"] * 0.88
            ) / 100.0
            campaign_conversion = (
                row["search_campaign_pct"] * 1.12
                + row["social_campaign_pct"] * 0.92
                + row["email_campaign_pct"] * 1.18
                + row["affiliate_campaign_pct"] * 0.95
            ) / 100.0
            acquisition_quality = (
                row["google_source_pct"] * 1.12
                + row["instagram_source_pct"] * 0.93
                + row["facebook_source_pct"] * 0.86
                + row["email_source_pct"] * 1.18
                + row["organic_source_pct"] * 1.23
                + row["referral_source_pct"] * 1.08
            ) / 100.0

            traffic_noise = rng.lognormal(mean=0.0, sigma=0.06)
            traffic = (
                row["_base_demand"]
                * 18.0
                * row["_demand_factor"]
                * row["_trend_factor"]
                * (0.55 + 0.45 * spend_index)
                * channel_reach
                * traffic_noise
            )
            traffic = max(25.0, traffic)

            active_rate = np.clip(
                0.24
                + 0.0012 * discount
                + 0.035 * row["website_sales_pct"] / 100.0
                + 0.050 * row["mobile_app_sales_pct"] / 100.0
                + rng.normal(0, 0.008),
                0.16,
                0.46,
            )
            active_users = traffic * active_rate

            current_ctr = np.clip(
                row["_base_ctr"] * campaign_ctr * (1.0 + discount / 220.0) * rng.normal(1.0, 0.045),
                0.006,
                0.085,
            )
            conversion_rate = (
                row["_base_conversion"]
                * price_effect
                * discount_effect
                * shipping_effect
                * channel_conversion
                * campaign_conversion
                * acquisition_quality
                * (0.97 + 0.06 * np.tanh((lagged_orders - 4) / 15))
            )
            conversion_rate = float(np.clip(conversion_rate * rng.normal(1.0, 0.045), 0.004, 0.145))

            unconstrained_orders = active_users * conversion_rate
            inventory_pressure = np.clip(inventory / max(unconstrained_orders, 1.0), 0.0, 1.0)
            orders = min(unconstrained_orders, inventory) * rng.normal(1.0, 0.025)
            orders = max(0.0, orders)
            lagged_orders = 0.62 * lagged_orders + 0.38 * orders

            revenue = orders * net_price
            marketplace_fee = revenue * (1.0 - channel_margin) * 0.55
            shipping_subsidy = orders * max(0.0, 49.0 - shipping_fee) * (
                row["website_sales_pct"] + row["mobile_app_sales_pct"]
            ) / 100.0
            gross_cost = orders * row["_unit_cost"]
            profit = revenue - gross_cost - spend - marketplace_fee - shipping_subsidy
            current_roas = revenue / max(spend, 1.0)

            retention_rate = (
                row["_base_retention"]
                * (0.96 + 0.08 * row["email_campaign_pct"] / 100.0)
                * (0.96 + 0.11 * row["organic_source_pct"] / 100.0)
                * (0.94 + 0.09 * inventory_pressure)
                * (1.0 - min(shipping_fee / max(price, 1.0), 0.16))
            )
            retention_rate = float(np.clip(retention_rate * rng.normal(1.0, 0.025), 0.12, 0.72))
            avg_ltv = row["_base_ltv"] * (0.74 + retention_rate) * (0.94 + 0.12 * channel_margin)

            row.update(
                {
                    "avg_ltv": round_money(avg_ltv),
                    "traffic": int(round(traffic)),
                    "active_users": int(round(active_users)),
                    "current_ctr": round(float(current_ctr), 4),
                    "current_roas": round(float(current_roas), 3),
                    "orders": int(round(orders)),
                    "revenue": round_money(revenue),
                    "profit": round_money(profit),
                    "conversion_rate": round(float(conversion_rate), 4),
                    "retention_rate": round(float(retention_rate), 4),
                }
            )
            metric_rows.append(row)

    return pd.DataFrame(metric_rows)


def metric_mean(df, product_id, metric, start_date, end_date):
    window = df[(df["product_id"] == product_id) & (df["date"] >= start_date) & (df["date"] <= end_date)]
    if metric in ["sales_channel_mix", "campaign_mix", "acquisition_mix", "dominant_age_group"]:
        return np.nan
    return float(window[metric].mean())


def finalize_experiments(df, experiments):
    rows = []
    for exp in experiments.to_dict("records"):
        start_date = exp["start_date"]
        end_date = exp["end_date"]
        baseline_start = max(DATE_START, start_date - pd.Timedelta(days=21))
        baseline_end = start_date - pd.Timedelta(days=1)
        metric = exp["primary_metric"]
        product_id = exp["product_id"]

        observed = metric_mean(df, product_id, metric, start_date, end_date)
        baseline = metric_mean(df, product_id, metric, baseline_start, baseline_end)
        if not np.isfinite(baseline) or abs(baseline) < 1e-9:
            baseline = metric_mean(df, product_id, metric, DATE_START, DATE_END)

        effect_pct = 0.0 if not np.isfinite(baseline) or abs(baseline) < 1e-9 else (observed - baseline) / abs(baseline) * 100.0
        if exp["expected_direction"] == "Increase":
            aligned = effect_pct > 1.5
        elif exp["expected_direction"] == "Decrease":
            aligned = effect_pct < -1.5
        else:
            aligned = abs(effect_pct) <= 1.5

        confidence = np.clip(0.58 + min(abs(effect_pct), 35) / 100 + rng.normal(0, 0.045), 0.52, 0.96)
        result = "Win" if aligned and confidence >= 0.62 else "Loss" if not aligned and confidence >= 0.62 else "Inconclusive"

        exp["observed_effect_pct"] = round(float(effect_pct), 2)
        exp["result"] = result
        exp["confidence"] = round(float(confidence), 3)
        exp["changed_features"] = json_dumps(exp["changed_features"])
        exp["start_date"] = start_date.strftime("%Y-%m-%d")
        exp["end_date"] = end_date.strftime("%Y-%m-%d")
        exp.pop("_scalar_updates", None)
        exp.pop("_mix_updates", None)
        rows.append(exp)

    return pd.DataFrame(rows)


def serialize_temporal(df):
    out = df.copy()
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    for column in ["sales_channel_mix", "campaign_mix", "acquisition_mix"]:
        out[column] = out[column].map(json_dumps)
    for column in [
        "avg_ltv",
        "inventory_available",
        "avg_selling_price",
        "discount_pct",
        "shipping_fee",
        "marketing_spend",
        "traffic",
        "active_users",
        "orders",
    ]:
        out[column] = out[column].round(0).astype(int)
    money_cols = ["revenue", "profit"]
    for column in money_cols:
        out[column] = out[column].round(2)
    return out[TEMPORAL_COLUMNS]


def build_data_dictionary(temporal_df, experiment_df):
    descriptions = {
        "date": "Daily observation date.",
        "product_id": "Stable product identifier shared across datasets.",
        "category": "Beauty and personal care category.",
        "subcategory": "Product subcategory mapped to category.",
        "brand": "D2C beauty brand.",
        "avg_ltv": "Estimated average customer lifetime value associated with the product on that date.",
        "dominant_age_group": "Dominant age band for product demand.",
        "inventory_available": "Daily available selling capacity or units in stock.",
        "avg_selling_price": "Listed average selling price before discount.",
        "discount_pct": "Average discount percentage applied.",
        "shipping_fee": "Customer-facing shipping fee.",
        "sales_channel_mix": "JSON percentage mix of sales channels; keys can evolve over time.",
        "campaign_mix": "JSON percentage mix of campaign types; keys can evolve over time.",
        "acquisition_mix": "JSON percentage mix of acquisition sources; keys can evolve over time.",
        "marketing_spend": "Daily marketing spend for the product.",
        "traffic": "Daily product-level traffic influenced by seasonality, spend, and channel mix.",
        "active_users": "Engaged visitors or active product users derived from traffic quality.",
        "current_ctr": "Current click-through rate for product campaigns.",
        "current_roas": "Revenue divided by marketing spend.",
        "orders": "Daily orders after conversion and inventory constraints.",
        "revenue": "Net revenue after discount.",
        "profit": "Estimated profit after cost, spend, fees, and shipping subsidy.",
        "conversion_rate": "Active user to order conversion rate.",
        "retention_rate": "Estimated retention rate influenced by product, channel, inventory, and lifecycle mix.",
        "experiment_id": "Stable experiment identifier.",
        "experiment_type": "Experiment family or strategy type.",
        "start_date": "Experiment start date within the configured timeline.",
        "end_date": "Experiment end date within the configured timeline.",
        "changed_features": "JSON object with exact tested feature changes.",
        "primary_metric": "Main temporal dataset field evaluated for the experiment.",
        "expected_direction": "Expected direction for the primary metric.",
        "observed_effect_pct": "Observed percentage lift or decline versus pre-period baseline.",
        "result": "Win, Loss, or Inconclusive based on observed direction and confidence.",
        "confidence": "Synthetic confidence score for experiment readout.",
        "notes": "Plain-language explanation of the experiment design.",
    }

    target_cols = {"orders", "revenue", "profit", "conversion_rate", "retention_rate", "current_roas", "observed_effect_pct", "result"}
    json_cols = {"sales_channel_mix", "campaign_mix", "acquisition_mix", "changed_features"}
    categorical_cols = {"category", "subcategory", "brand", "dominant_age_group", "experiment_type", "expected_direction", "result"}
    date_cols = {"date", "start_date", "end_date"}
    bool_cols = set()

    rows = []
    for dataset_name, dataset in [("temporal_dataset.csv", temporal_df), ("experiment_dataset.csv", experiment_df)]:
        for column in dataset.columns:
            if column in json_cols:
                data_type = "json"
            elif column in date_cols:
                data_type = "date"
            elif column in bool_cols:
                data_type = "boolean"
            elif column in categorical_cols or dataset[column].dtype == "object":
                data_type = "categorical"
            elif pd.api.types.is_integer_dtype(dataset[column]):
                data_type = "integer"
            else:
                data_type = "float"

            rows.append(
                {
                    "column_name": column,
                    "dataset": dataset_name,
                    "data_type": data_type,
                    "description": descriptions.get(column, f"{column} field in {dataset_name}."),
                    "is_feature": column not in target_cols,
                    "is_target": column in target_cols,
                    "example_value": str(dataset[column].iloc[0]),
                }
            )

    return pd.DataFrame(rows)


def validate_json_sums(serialized_temporal):
    results = {}
    for column in ["sales_channel_mix", "campaign_mix", "acquisition_mix"]:
        sums = serialized_temporal[column].map(lambda x: round(sum(json.loads(x).values()), 2))
        results[column] = {
            "min_sum": float(sums.min()),
            "max_sum": float(sums.max()),
            "invalid_rows": int((np.abs(sums - 100.0) > 0.01).sum()),
        }
    return results


def validate_flattened_sums(serialized_temporal):
    groups = {
        "sales_channel_flattened": list(SALES_FLAT.values()),
        "campaign_flattened": list(CAMPAIGN_FLAT.values()),
        "acquisition_flattened": list(ACQUISITION_FLAT.values()),
    }
    results = {}
    for name, columns in groups.items():
        sums = serialized_temporal[columns].sum(axis=1).round(2)
        results[name] = {
            "min_sum": float(sums.min()),
            "max_sum": float(sums.max()),
            "invalid_rows": int((np.abs(sums - 100.0) > 0.01).sum()),
        }
    return results


def validate_experiment_reflection(temporal_df, experiment_df):
    temporal_dates = temporal_df.assign(date=pd.to_datetime(temporal_df["date"]))
    checks = []
    for exp in experiment_df.to_dict("records"):
        product_id = exp["product_id"]
        start_date = pd.Timestamp(exp["start_date"])
        changed = json.loads(exp["changed_features"])
        start_row = temporal_dates[
            (temporal_dates["product_id"] == product_id) & (temporal_dates["date"] == start_date)
        ].iloc[0]

        reflected = True
        for feature, detail in changed.items():
            if feature in ["sales_channel_mix", "campaign_mix", "acquisition_mix"]:
                mix = json.loads(start_row[feature])
                for key, key_detail in detail.items():
                    reflected &= abs(float(mix.get(key, 0.0)) - float(key_detail["new"])) <= 0.05
            else:
                reflected &= abs(float(start_row[feature]) - float(detail["new"])) <= max(1.0, abs(float(detail["new"])) * 0.015)
        checks.append(reflected)
    return {
        "checked_experiments": len(checks),
        "reflected_experiments": int(sum(checks)),
        "failed_experiments": int(len(checks) - sum(checks)),
    }


def print_validation(temporal_df, experiment_df, dictionary_df):
    expected_temporal_rows = num_products * NUM_DAYS
    expected_experiment_rows = experiments_per_family * len(EXPERIMENT_TYPES)
    print("Row counts")
    print(
        pd.Series(
            {
                "temporal_dataset.csv": len(temporal_df),
                "experiment_dataset.csv": len(experiment_df),
                "data_dictionary.csv": len(dictionary_df),
                "expected_temporal_rows": expected_temporal_rows,
                "expected_experiment_rows": expected_experiment_rows,
            }
        ).to_string()
    )
    print("\nNull counts: temporal_dataset.csv")
    print(temporal_df.isna().sum().to_string())
    print("\nNull counts: experiment_dataset.csv")
    print(experiment_df.isna().sum().to_string())
    print("\nJSON mix sum validation")
    print(json.dumps(validate_json_sums(temporal_df), indent=2))
    print("\nFlattened mix sum validation")
    print(json.dumps(validate_flattened_sums(temporal_df), indent=2))
    print("\nExperiment counts by experiment_type")
    print(experiment_df["experiment_type"].value_counts().sort_index().to_string())
    print("\nExperiment product_id existence")
    print(bool(set(experiment_df["product_id"]).issubset(set(temporal_df["product_id"]))))
    print("\nExperiment date range existence")
    temporal_dates = temporal_df.assign(date=pd.to_datetime(temporal_df["date"]))
    range_exists = []
    for exp in experiment_df.to_dict("records"):
        mask = (
            (temporal_dates["product_id"] == exp["product_id"])
            & (temporal_dates["date"] >= pd.Timestamp(exp["start_date"]))
            & (temporal_dates["date"] <= pd.Timestamp(exp["end_date"]))
        )
        expected_days = (pd.Timestamp(exp["end_date"]) - pd.Timestamp(exp["start_date"])).days + 1
        range_exists.append(int(mask.sum()) == expected_days)
    print({"checked_experiments": len(range_exists), "valid_ranges": int(sum(range_exists)), "invalid_ranges": int(len(range_exists) - sum(range_exists))})
    print("\nChanged features reflected in temporal_dataset.csv")
    print(validate_experiment_reflection(temporal_df, experiment_df))


def main():
    products = create_products(n_products=num_products)
    baseline = build_temporal_baseline(products)
    experiments_with_plans = create_experiments(baseline, products, experiments_per_family)
    experimented = apply_experiments(baseline, experiments_with_plans)
    modeled = recompute_metrics(experimented)
    temporal_df = serialize_temporal(modeled)
    experiment_df = finalize_experiments(modeled, experiments_with_plans)
    dictionary_df = build_data_dictionary(temporal_df, experiment_df)

    temporal_df.to_csv(OUTPUT_TEMPORAL, index=False)
    experiment_df.to_csv(OUTPUT_EXPERIMENT, index=False)
    dictionary_df.to_csv(OUTPUT_DICTIONARY, index=False)

    print_validation(temporal_df, experiment_df, dictionary_df)


if __name__ == "__main__":
    main()
