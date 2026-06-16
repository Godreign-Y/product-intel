"""
Action Schedule Generator Module.

Generates simulated promotional, marketing, and operational action schedules
for various products across a year.
"""

import json
import random
import uuid
from typing import Any, Dict, List, Callable

random.seed(42)

# =====================================================
# CONFIG
# =====================================================

# Reduced from 10 products to 6 products
PRODUCTS: List[str] = [f"P{i:03}" for i in range(1, 7)]

# Reduced from 12 anchors to 4 quarterly anchors
ANCHORS: List[int] = [
    90,
    180,
    270,
    360
]

# =====================================================
# FEATURE DEFINITIONS
# =====================================================

PRICE_FEATURES: List[str] = [
    "avg_selling_price"
]

DISCOUNT_FEATURES: List[str] = [
    "discount_pct"
]

SHIPPING_FEATURES: List[str] = [
    "shipping_fee"
]

INVENTORY_FEATURES: List[str] = [
    "inventory_available"
]

MARKETING_FEATURES: List[str] = [
    "marketing_spend"
]

CHANNELS: List[str] = [
    "amazon",
    "website",
    "nykaa",
    "mobile_app"
]

CAMPAIGNS: List[str] = [
    "search",
    "social",
    "email",
    "affiliate"
]

ACQUISITION: List[str] = [
    "google",
    "instagram",
    "facebook",
    "organic",
    "referral",
    "email"
]

# =====================================================
# EVENT GENERATORS
# =====================================================

def generate_price_event(day: int) -> Dict[str, Any]:
    """
    Generate a price change event.

    Args:
        day (int): The relative day for the event.

    Returns:
        Dict[str, Any]: The event payload containing feature, operation, and delta.
    """
    return {
        "event_id": str(uuid.uuid4()),
        "relative_day": day,
        "feature": "avg_selling_price",
        "operation": "relative_pct",
        "delta": random.choice([-40, -30, -20, -10, -5, 5, 10, 20, 30, 40]),
        "duration_days": random.randint(90, 365)
    }


def generate_discount_event(day: int) -> Dict[str, Any]:
    """
    Generate a discount event.

    Args:
        day (int): The relative day for the event.

    Returns:
        Dict[str, Any]: The event payload containing feature, operation, and delta.
    """
    return {
        "event_id": str(uuid.uuid4()),
        "relative_day": day,
        "feature": "discount_pct",
        "operation": "relative_pct",
        "delta": random.choice([-50, -40, -30, -20, -10, 10, 20, 30, 40, 50]),
        "duration_days": random.randint(7, 90)
    }


def generate_shipping_event(day: int) -> Dict[str, Any]:
    """
    Generate a shipping fee change event.

    Args:
        day (int): The relative day for the event.

    Returns:
        Dict[str, Any]: The event payload containing feature, operation, and delta.
    """
    return {
        "event_id": str(uuid.uuid4()),
        "relative_day": day,
        "feature": "shipping_fee",
        "operation": "relative_pct",
        "delta": random.choice([-50, -25, -10, 10, 25, 50, 100]),
        "duration_days": random.randint(30, 365)
    }


def generate_inventory_event(day: int) -> Dict[str, Any]:
    """
    Generate an inventory change event.

    Args:
        day (int): The relative day for the event.

    Returns:
        Dict[str, Any]: The event payload containing feature, operation, and delta.
    """
    return {
        "event_id": str(uuid.uuid4()),
        "relative_day": day,
        "feature": "inventory_available",
        "operation": "relative_pct",
        "delta": random.choice([-80, -50, -20, 20, 50, 100, 200, 300]),
        "duration_days": random.randint(1, 30)
    }


def generate_marketing_event(day: int) -> Dict[str, Any]:
    """
    Generate a marketing spend change event.

    Args:
        day (int): The relative day for the event.

    Returns:
        Dict[str, Any]: The event payload containing feature, operation, and delta.
    """
    return {
        "event_id": str(uuid.uuid4()),
        "relative_day": day,
        "feature": "marketing_spend",
        "operation": "relative_pct",
        "delta": random.choice([-80, -50, -20, 20, 50, 100, 200, 300]),
        "duration_days": random.randint(7, 120)
    }


def generate_channel_shift(day: int) -> Dict[str, Any]:
    """
    Generate a sales channel mix shift event.

    Args:
        day (int): The relative day for the event.

    Returns:
        Dict[str, Any]: The event payload containing feature, operation, source, target, and delta.
    """
    src, dst = random.sample(CHANNELS, 2)

    return {
        "event_id": str(uuid.uuid4()),
        "relative_day": day,
        "feature": "sales_channel_mix",
        "operation": "mix_shift",
        "source": src,
        "target": dst,
        "delta": random.choice([5, 10, 15, 20, 25, 30]),
        "duration_days": random.randint(30, 365)
    }


def generate_campaign_shift(day: int) -> Dict[str, Any]:
    """
    Generate a campaign mix shift event.

    Args:
        day (int): The relative day for the event.

    Returns:
        Dict[str, Any]: The event payload containing feature, operation, source, target, and delta.
    """
    src, dst = random.sample(CAMPAIGNS, 2)

    return {
        "event_id": str(uuid.uuid4()),
        "relative_day": day,
        "feature": "campaign_mix",
        "operation": "mix_shift",
        "source": src,
        "target": dst,
        "delta": random.choice([5, 10, 15, 20, 25, 30]),
        "duration_days": random.randint(14, 120)
    }


def generate_acquisition_shift(day: int) -> Dict[str, Any]:
    """
    Generate an acquisition mix shift event.

    Args:
        day (int): The relative day for the event.

    Returns:
        Dict[str, Any]: The event payload containing feature, operation, source, target, and delta.
    """
    src, dst = random.sample(ACQUISITION, 2)

    return {
        "event_id": str(uuid.uuid4()),
        "relative_day": day,
        "feature": "acquisition_mix",
        "operation": "mix_shift",
        "source": src,
        "target": dst,
        "delta": random.choice([5, 10, 15, 20, 25, 30]),
        "duration_days": random.randint(30, 365)
    }


# =====================================================
# MASTER EVENT FACTORY
# =====================================================

EVENT_GENERATORS: List[Callable[[int], Dict[str, Any]]] = [
    generate_price_event,
    generate_discount_event,
    generate_shipping_event,
    generate_inventory_event,
    generate_marketing_event,
    generate_channel_shift,
    generate_campaign_shift,
    generate_acquisition_shift
]

# =====================================================
# SCHEDULE CREATION
# =====================================================

def sample_day() -> int:
    """
    Sample a random day of the year.

    Returns:
        int: A random integer representing a day of the year (0-365).
    """
    return random.randint(0, 365)


def generate_schedule(complexity: str) -> List[Dict[str, Any]]:
    """
    Generate a schedule of events based on complexity.

    Args:
        complexity (str): The complexity level of the schedule.

    Returns:
        List[Dict[str, Any]]: A list of generated events sorted by relative_day.
    """

    if complexity == "simple":
        n_events = 1
    elif complexity == "medium":
        n_events = random.randint(2, 3)
    elif complexity == "complex":
        n_events = random.randint(4, 6)
    else:  # stress
        n_events = random.randint(7, 15)

    events: List[Dict[str, Any]] = []

    for _ in range(n_events):
        generator = random.choice(EVENT_GENERATORS)
        events.append(generator(sample_day()))

    events = sorted(events, key=lambda x: x["relative_day"])
    return events


# =====================================================
# MAIN
# =====================================================

def main() -> None:
    """
    Main function to generate and save action schedules.
    """

    schedules: List[Dict[str, Any]] = []

    for product_id in PRODUCTS:
        for anchor in ANCHORS:

            # 10 schedules per product-anchor:
            # 4 simple + 3 medium + 2 complex + 1 stress
            complexity_mix: List[str] = (
                ["simple"] * 4 +
                ["medium"] * 3 +
                ["complex"] * 2 +
                ["stress"] * 1
            )

            for complexity in complexity_mix:
                schedules.append({
                    "schedule_id": str(uuid.uuid4()),
                    "product_id": product_id,
                    "anchor_day": anchor,
                    "complexity": complexity,
                    "events": generate_schedule(complexity)
                })

    output_file: str = "action_schedules.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(schedules, f, indent=2)

    print(f"Saved: {output_file}")
    print(f"Generated {len(schedules)} schedules")


if __name__ == "__main__":
    main()