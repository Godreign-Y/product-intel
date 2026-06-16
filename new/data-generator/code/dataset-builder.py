import json
from pathlib import Path

import numpy as np
import pandas as pd


TRAJECTORY_FILE = "final-output/trajectories_v8.csv"
SCHEDULE_FILE = "action_schedules.json"

OUTPUT_FILE = "final-output/training_dataset.csv"


# --------------------------------------------------
# CONFIG
# --------------------------------------------------

ACTION_FEATURES = [
    "avg_selling_price",
    "discount_pct",
    "shipping_fee",
    "marketing_spend",
    "inventory_available",
]

MIX_FEATURES = [
    "sales_channel_mix",
    "campaign_mix",
    "acquisition_mix",
]

TARGET_COLS = [
    "traffic",
    "active_users",
    "orders",
    "revenue",
    "profit",
    "conversion_rate",
    "retention_rate",
    "avg_ltv",
]


# --------------------------------------------------
# BUILD EVENT LOOKUP
# --------------------------------------------------

def build_event_lookup(schedules):
    """
    Returns:

    lookup[schedule_id][day] -> list(events starting on day)
    """

    lookup = {}

    for schedule in schedules:

        sid = schedule["schedule_id"]

        lookup[sid] = {}

        for event in schedule["events"]:

            day = event["relative_day"]

            lookup[sid].setdefault(day, [])
            lookup[sid][day].append(event)

    return lookup


# --------------------------------------------------
# BUILD AGE FEATURES
# --------------------------------------------------

def compute_age_features(schedule_events, max_day):
    """
    Creates age arrays for each schedule.

    Returns:

    age_table[day]
    """

    age_rows = []

    for day in range(max_day + 1):

        row = {
            "price_age": -1,
            "discount_age": -1,
            "shipping_fee_age": -1,
            "marketing_spend_age": -1,
            "inventory_available_age": -1,
            "sales_channel_mix_age": -1,
            "campaign_mix_age": -1,
            "acquisition_mix_age": -1,
        }

        for event in schedule_events:

            start = event["relative_day"]
            duration = event["duration_days"]

            end = start + duration

            if not (start <= day <= end):
                continue

            age = day - start

            feature = event["feature"]

            if feature == "avg_selling_price":
                row["price_age"] = age

            elif feature == "discount_pct":
                row["discount_age"] = age

            elif feature == "shipping_fee":
                row["shipping_fee_age"] = age

            elif feature == "marketing_spend":
                row["marketing_spend_age"] = age

            elif feature == "inventory_available":
                row["inventory_available_age"] = age

            elif "sales" in feature:
                row["sales_channel_mix_age"] = age

            elif "campaign" in feature:
                row["campaign_mix_age"] = age

            elif "acq" in feature or "acquisition" in feature:
                row["acquisition_mix_age"] = age

        age_rows.append(row)

    return age_rows


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():

    print("Loading trajectories...")
    df = pd.read_csv(TRAJECTORY_FILE)

    print("Loading schedules...")
    with open(SCHEDULE_FILE, "r") as f:
        schedules = json.load(f)

    schedule_map = {
        s["schedule_id"]: s
        for s in schedules
    }

    print("Building age tables...")

    age_lookup = {}

    for schedule in schedules:

        sid = schedule["schedule_id"]

        age_lookup[sid] = compute_age_features(
            schedule["events"],
            365
        )

    print("Generating transitions...")

    output_rows = []

    grouped = df.groupby(
        ["trajectory_id"],
        sort=False
    )

    total = len(grouped)

    for idx, (_, traj_df) in enumerate(grouped):

        traj_df = traj_df.sort_values("day")

        sid = traj_df["schedule_id"].iloc[0]

        ages = age_lookup[sid]

        rows = traj_df.to_dict("records")

        for i in range(len(rows) - 1):

            cur = rows[i]
            nxt = rows[i + 1]

            day = int(cur["day"])

            sample = {}

            # ------------------------------------
            # metadata
            # ------------------------------------

            sample["trajectory_id"] = cur["trajectory_id"]
            sample["schedule_id"] = cur["schedule_id"]
            sample["product_id"] = cur["product_id"]
            sample["day"] = day

            # ------------------------------------
            # current state
            # ------------------------------------

            for k, v in cur.items():

                if k in [
                    "trajectory_id",
                    "schedule_id",
                    "product_id",
                    "day",
                ]:
                    continue

                sample[k] = v

            # ------------------------------------
            # intervention ages
            # ------------------------------------

            age_row = ages[day]

            sample.update(age_row)

            # ------------------------------------
            # targets
            # ------------------------------------

            for col in TARGET_COLS:

                sample[f"next_{col}"] = nxt[col]

            output_rows.append(sample)

        if (idx + 1) % 100 == 0:

            print(
                f"{idx + 1}/{total} trajectories processed"
            )

    out_df = pd.DataFrame(output_rows)

    print(f"Rows generated: {len(out_df):,}")

    out_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()