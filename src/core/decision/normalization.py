"""Shared driver/KPI normalization for decision pipeline modules."""

from typing import Dict

DRIVER_ALIASES: Dict[str, str] = {
    "discount": "discount_pct",
    "discount %": "discount_pct",
    "discount percentage": "discount_pct",
    "discounts": "discount_pct",
    "discount_pct": "discount_pct",
    "promo": "discount_pct",
    "promotion": "discount_pct",
    "price": "avg_selling_price",
    "pricing": "avg_selling_price",
    "selling price": "avg_selling_price",
    "average price": "avg_selling_price",
    "avg price": "avg_selling_price",
    "avg_selling_price": "avg_selling_price",
    "shipping": "shipping_fee",
    "shipping fee": "shipping_fee",
    "fulfillment fee": "shipping_fee",
    "delivery fee": "shipping_fee",
    "shipping_fee": "shipping_fee",
    "marketing": "marketing_spend",
    "marketing spend": "marketing_spend",
    "ad spend": "marketing_spend",
    "ads": "marketing_spend",
    "spend": "marketing_spend",
    "advertising": "marketing_spend",
    "marketing_spend": "marketing_spend",
    "inventory_available": "inventory_available",
    "inventory": "inventory_available",
    "stock": "inventory_available",
}

KPI_ALIASES: Dict[str, str] = {
    "revenue": "revenue",
    "total_revenue": "revenue",
    "total revenue": "revenue",
    "profit": "profit",
    "total_profit": "profit",
    "total profit": "profit",
    "margin": "profit",
    "orders": "orders",
    "total_orders": "orders",
    "total orders": "orders",
    "sales volume": "orders",
    "conversion_rate": "conversion_rate",
    "mean_conversion_rate": "conversion_rate",
    "mean conversion rate": "conversion_rate",
    "conversion": "conversion_rate",
    "checkout": "conversion_rate",
    "ctr": "conversion_rate",
    "retention_rate": "retention_rate",
    "mean_retention_rate": "retention_rate",
    "mean retention rate": "retention_rate",
    "retention": "retention_rate",
}


def normalize_driver(driver: str) -> str:
    if not driver:
        return ""
    d_clean = driver.lower().replace("_", " ").strip()
    if driver.lower() in DRIVER_ALIASES:
        return DRIVER_ALIASES[driver.lower()]
    if d_clean in DRIVER_ALIASES:
        return DRIVER_ALIASES[d_clean]
    for k, v in DRIVER_ALIASES.items():
        if k in d_clean or d_clean in k:
            return v
    return driver.lower()


def normalize_kpi(kpi: str) -> str:
    if not kpi:
        return ""
    k_clean = kpi.lower().replace("_", " ").strip()
    if kpi.lower() in KPI_ALIASES:
        return KPI_ALIASES[kpi.lower()]
    if k_clean in KPI_ALIASES:
        return KPI_ALIASES[k_clean]
    for k, v in KPI_ALIASES.items():
        if k in k_clean or k_clean in k:
            return v
    return kpi.lower()
