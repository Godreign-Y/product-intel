# prepare_tft_data.py

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split


# ============================================================
# CONFIG
# ============================================================

RAW_CSV = "training_dataset.csv"

OUTPUT_DIR = Path("prepared_tft")
OUTPUT_DIR.mkdir(exist_ok=True)

RANDOM_SEED = 42

TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15


# ============================================================
# LOAD
# ============================================================

print("Loading dataset...")

df = pd.read_csv(RAW_CSV)

print(f"Rows: {len(df):,}")


# ============================================================
# BASIC VALIDATION
# ============================================================

print("Running validation...")

if df.isnull().sum().sum() > 0:
    raise ValueError(
        f"Dataset contains {df.isnull().sum().sum()} null values"
    )

required_columns = [
    "trajectory_id",
    "day",
    "product_id",
    "category_id"
]

for c in required_columns:
    if c not in df.columns:
        raise ValueError(f"Missing required column: {c}")

print("Required columns OK")


# ============================================================
# VALIDATE TRAJECTORIES
# ============================================================

trajectory_lengths = (
    df.groupby("trajectory_id")
      .size()
      .reset_index(name="rows")
)

bad = trajectory_lengths[
    trajectory_lengths["rows"] != 364
]

if len(bad) > 0:
    print(bad.head())
    raise ValueError(
        f"Found {len(bad)} trajectories with !=364 rows"
    )

print(
    f"All {len(trajectory_lengths)} trajectories "
    f"have 364 rows"
)

# ============================================================
# SORT
# ============================================================

df = df.sort_values(
    ["trajectory_id", "day"]
).reset_index(drop=True)

# ============================================================
# TFT REQUIRED COLUMNS
# ============================================================

df["group_id"] = df["trajectory_id"]
df["time_idx"] = df["day"]

# categorical columns should be strings
df["product_id"] = df["product_id"].astype(str)
df["category_id"] = df["category_id"].astype(str)

# ============================================================
# SPLIT TRAJECTORIES
# ============================================================

all_trajectories = (
    df["trajectory_id"]
    .drop_duplicates()
    .tolist()
)

train_traj, temp_traj = train_test_split(
    all_trajectories,
    test_size=0.30,
    random_state=RANDOM_SEED,
    shuffle=True
)

val_traj, test_traj = train_test_split(
    temp_traj,
    test_size=0.50,
    random_state=RANDOM_SEED,
    shuffle=True
)

print()
print("Trajectory Split")
print("--------------------------")
print(f"Train: {len(train_traj)}")
print(f"Val:   {len(val_traj)}")
print(f"Test:  {len(test_traj)}")

# ============================================================
# CREATE SPLITS
# ============================================================

train_df = df[
    df["trajectory_id"].isin(train_traj)
].copy()

val_df = df[
    df["trajectory_id"].isin(val_traj)
].copy()

test_df = df[
    df["trajectory_id"].isin(test_traj)
].copy()

print()
print("Row Counts")
print("--------------------------")
print(f"Train: {len(train_df):,}")
print(f"Val:   {len(val_df):,}")
print(f"Test:  {len(test_df):,}")

# ============================================================
# SAVE PARQUET
# ============================================================

train_path = OUTPUT_DIR / "train.parquet"
val_path = OUTPUT_DIR / "val.parquet"
test_path = OUTPUT_DIR / "test.parquet"

train_df.to_parquet(train_path, index=False)
val_df.to_parquet(val_path, index=False)
test_df.to_parquet(test_path, index=False)

print()
print("Saved parquet files")

# ============================================================
# SAVE SPLIT METADATA
# ============================================================

pd.DataFrame({
    "trajectory_id": train_traj,
    "split": "train"
}).to_csv(
    OUTPUT_DIR / "train_trajectories.csv",
    index=False
)

pd.DataFrame({
    "trajectory_id": val_traj,
    "split": "val"
}).to_csv(
    OUTPUT_DIR / "val_trajectories.csv",
    index=False
)

pd.DataFrame({
    "trajectory_id": test_traj,
    "split": "test"
}).to_csv(
    OUTPUT_DIR / "test_trajectories.csv",
    index=False
)

print()
print("Done.")
print(f"Output directory: {OUTPUT_DIR}")
