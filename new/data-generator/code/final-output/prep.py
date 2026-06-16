import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


# ============================================================
# CONFIG
# ============================================================

INPUT_FILE = (
    r"C:\code\Product_intel\new\data-generator"
    r"\code\final-output\training_dataset.csv"
)

ARTIFACT_DIR = Path("artifacts")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

RANDOM_STATE = 42

ENCODER_LEN = 30
DECODER_LEN = 30
PRED_LEN = 30

DAY_COL = "day"
TRAJECTORY_COL = "trajectory_id"
PRODUCT_COL = "product_id"
CATEGORY_COL = "category_id"


# ============================================================
# TARGETS
# ============================================================

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


# ============================================================
# DECODER FEATURES
# ============================================================

BASE_DECODER_FEATURES = [
    "inventory_available",
    "avg_selling_price",
    "effective_price",
    "discount_pct",
    "shipping_fee",
    "marketing_spend",
]

DECODER_AGE_FEATURES = [
    "price_age",
    "discount_age",
    "shipping_fee_age",
    "marketing_spend_age",
    "inventory_available_age",
    "sales_channel_mix_age",
    "campaign_mix_age",
    "acquisition_mix_age",
]


# ============================================================
# SAVE HELPERS
# ============================================================

def save_json(obj, path):

    with open(path, "w") as f:
        json.dump(obj, f, indent=4)


def save_pickle(obj, path):

    with open(path, "wb") as f:
        pickle.dump(obj, f)


# ============================================================
# VALIDATION
# ============================================================

def validate_schema(df):

    required_cols = [
        TRAJECTORY_COL,
        PRODUCT_COL,
        CATEGORY_COL,
        DAY_COL,
    ]

    missing = [
        c
        for c in required_cols
        if c not in df.columns
    ]

    if len(missing) > 0:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    target_missing = [
        c
        for c in TARGET_COLS
        if c not in df.columns
    ]

    if len(target_missing) > 0:
        raise ValueError(
            f"Missing target columns: {target_missing}"
        )


def validate_nulls(df):

    null_counts = (
        df.isnull()
        .sum()
    )

    null_counts = (
        null_counts[
            null_counts > 0
        ]
    )

    if len(null_counts) > 0:

        print("\nMissing values found:\n")
        print(null_counts)

        raise ValueError(
            "Dataset contains null values."
        )


def validate_trajectories(df):

    lengths = (
        df.groupby(
            TRAJECTORY_COL
        )
        .size()
    )

    print("\nTrajectory Stats")
    print(lengths.describe())

    min_required = (
        ENCODER_LEN +
        PRED_LEN
    )

    if lengths.min() < min_required:

        raise ValueError(
            f"Found trajectory shorter than "
            f"{min_required} days."
        )


# ============================================================
# VOCABS
# ============================================================

def build_vocab(series):

    unique_values = sorted(
        series.astype(str)
        .unique()
        .tolist()
    )

    vocab = {
        token: idx
        for idx, token
        in enumerate(unique_values)
    }

    return vocab


def encode_static_ids(
    df,
    product_vocab,
    category_vocab
):

    df[PRODUCT_COL] = (
        df[PRODUCT_COL]
        .astype(str)
        .map(product_vocab)
    )

    df[CATEGORY_COL] = (
        df[CATEGORY_COL]
        .astype(str)
        .map(category_vocab)
    )

    return df


# ============================================================
# DECODER FEATURE DISCOVERY
# ============================================================

def discover_decoder_features(df):

    sales_mix_cols = [
        c
        for c in df.columns
        if c.startswith(
            "sales_mix_"
        )
    ]

    campaign_mix_cols = [
        c
        for c in df.columns
        if c.startswith(
            "campaign_mix_"
        )
    ]

    acq_mix_cols = [
        c
        for c in df.columns
        if c.startswith(
            "acq_mix_"
        )
    ]

    age_mix_cols = [
        c
        for c in df.columns
        if c.startswith(
            "age_mix_"
        )
    ]

    decoder_cols = (
        BASE_DECODER_FEATURES
        + sales_mix_cols
        + campaign_mix_cols
        + acq_mix_cols
        + age_mix_cols
        + DECODER_AGE_FEATURES
    )

    missing = [
        c
        for c in decoder_cols
        if c not in df.columns
    ]

    if len(missing) > 0:
        raise ValueError(
            f"Missing decoder columns: "
            f"{missing}"
        )

    print("\nDecoder Features")
    print(
        f"Count = {len(decoder_cols)}"
    )

    return decoder_cols


# ============================================================
# ENCODER FEATURES
# ============================================================

def discover_encoder_features(df):

    excluded = {

        TRAJECTORY_COL,
        "schedule_id",

        PRODUCT_COL,
        CATEGORY_COL,

        DAY_COL,

        "group_id",
        "time_idx",

        "next_traffic",
        "next_active_users",
        "next_orders",
        "next_revenue",
        "next_profit",
        "next_conversion_rate",
        "next_retention_rate",
        "next_avg_ltv",
    }

    encoder_cols = []

    for col in df.columns:

        if col in excluded:
            continue

        if not pd.api.types.is_numeric_dtype(
            df[col]
        ):
            continue

        encoder_cols.append(col)

    print("\nEncoder Features")
    print(
        f"Count = {len(encoder_cols)}"
    )

    return encoder_cols


# ============================================================
# TRAJECTORY SPLIT
# ============================================================

def split_trajectories(df):

    trajectory_ids = sorted(
        df[
            TRAJECTORY_COL
        ]
        .unique()
        .tolist()
    )

    train_ids, temp_ids = (
        train_test_split(
            trajectory_ids,
            test_size=0.30,
            random_state=RANDOM_STATE,
        )
    )

    val_ids, test_ids = (
        train_test_split(
            temp_ids,
            test_size=0.50,
            random_state=RANDOM_STATE,
        )
    )

    assert (
        len(
            set(train_ids)
            &
            set(val_ids)
        )
        == 0
    )

    assert (
        len(
            set(train_ids)
            &
            set(test_ids)
        )
        == 0
    )

    assert (
        len(
            set(val_ids)
            &
            set(test_ids)
        )
        == 0
    )

    print("\nTrajectory Split")

    print(
        f"Train: {len(train_ids)}"
    )

    print(
        f"Val: {len(val_ids)}"
    )

    print(
        f"Test: {len(test_ids)}"
    )

    return (
        train_ids,
        val_ids,
        test_ids,
    )
# ============================================================
# WINDOW GENERATION
# ============================================================

def create_windows_for_trajectory(
    traj_df,
    encoder_cols,
    decoder_cols,
):

    samples = []

    traj_df = (
        traj_df
        .sort_values(DAY_COL)
        .reset_index(drop=True)
    )

    assert (
        traj_df[DAY_COL]
        .is_monotonic_increasing
    )

    total_len = len(traj_df)

    expected_windows = (
        total_len
        - ENCODER_LEN
        - PRED_LEN
        + 1
    )

    assert expected_windows > 0

    trajectory_id = (
        traj_df[TRAJECTORY_COL]
        .iloc[0]
    )

    product_id = (
        traj_df[PRODUCT_COL]
        .iloc[0]
    )

    category_id = (
        traj_df[CATEGORY_COL]
        .iloc[0]
    )

    print(
        f"{trajectory_id}: "
        f"{expected_windows} windows"
    )

    for start_idx in range(expected_windows):

        enc_start = start_idx
        enc_end = (
            start_idx +
            ENCODER_LEN
        )

        dec_start = enc_end
        dec_end = (
            dec_start +
            DECODER_LEN
        )

        encoder_x = (
            traj_df.iloc[
                enc_start:enc_end
            ][encoder_cols]
            .to_numpy(
                dtype=np.float32
            )
        )

        decoder_x = (
            traj_df.iloc[
                dec_start:dec_end
            ][decoder_cols]
            .to_numpy(
                dtype=np.float32
            )
        )

        target_y = (
            traj_df.iloc[
                dec_start:dec_end
            ][TARGET_COLS]
            .to_numpy(
                dtype=np.float32
            )
        )

        samples.append(
            {
                "encoder_x": encoder_x,
                "decoder_x": decoder_x,
                "target_y": target_y,

                "product_id":
                    product_id,

                "category_id":
                    category_id,

                "trajectory_id":
                    trajectory_id,
            }
        )

    return samples


def build_windows(
    df,
    encoder_cols,
    decoder_cols,
):

    samples = []

    grouped = (
        df.groupby(
            TRAJECTORY_COL,
            sort=False
        )
    )

    for (
        trajectory_id,
        traj_df
    ) in grouped:

        traj_samples = (
            create_windows_for_trajectory(
                traj_df,
                encoder_cols,
                decoder_cols,
            )
        )

        samples.extend(
            traj_samples
        )

    return samples


# ============================================================
# CONVERT TO ARRAYS
# ============================================================

def samples_to_arrays(samples):

    encoder_x = np.stack(
        [
            s["encoder_x"]
            for s in samples
        ]
    )

    decoder_x = np.stack(
        [
            s["decoder_x"]
            for s in samples
        ]
    )

    target_y = np.stack(
        [
            s["target_y"]
            for s in samples
        ]
    )

    product_id = np.array(
        [
            s["product_id"]
            for s in samples
        ]
    )

    category_id = np.array(
        [
            s["category_id"]
            for s in samples
        ]
    )

    trajectory_id = [
        s["trajectory_id"]
        for s in samples
    ]

    return {
        "encoder_x":
            encoder_x,

        "decoder_x":
            decoder_x,

        "target_y":
            target_y,

        "product_id":
            product_id,

        "category_id":
            category_id,

        "trajectory_id":
            trajectory_id,
    }


# ============================================================
# SCALERS
# ============================================================

def fit_scalers(train_data):

    encoder_scaler = (
        StandardScaler()
    )

    decoder_scaler = (
        StandardScaler()
    )

    target_scaler = (
        StandardScaler()
    )

    encoder_scaler.fit(
        train_data["encoder_x"]
        .reshape(
            -1,
            train_data[
                "encoder_x"
            ].shape[-1]
        )
    )

    decoder_scaler.fit(
        train_data["decoder_x"]
        .reshape(
            -1,
            train_data[
                "decoder_x"
            ].shape[-1]
        )
    )

    target_scaler.fit(
        train_data["target_y"]
        .reshape(
            -1,
            len(TARGET_COLS)
        )
    )

    return (
        encoder_scaler,
        decoder_scaler,
        target_scaler,
    )


# ============================================================
# SCALING
# ============================================================

def scale_dataset(
    data,
    encoder_scaler,
    decoder_scaler,
    target_scaler,
):

    enc_shape = (
        data["encoder_x"]
        .shape
    )

    dec_shape = (
        data["decoder_x"]
        .shape
    )

    tgt_shape = (
        data["target_y"]
        .shape
    )

    data["encoder_x"] = (
        encoder_scaler
        .transform(
            data["encoder_x"]
            .reshape(
                -1,
                enc_shape[-1]
            )
        )
        .reshape(enc_shape)
        .astype(np.float32)
    )

    data["decoder_x"] = (
        decoder_scaler
        .transform(
            data["decoder_x"]
            .reshape(
                -1,
                dec_shape[-1]
            )
        )
        .reshape(dec_shape)
        .astype(np.float32)
    )

    data["target_y"] = (
        target_scaler
        .transform(
            data["target_y"]
            .reshape(
                -1,
                tgt_shape[-1]
            )
        )
        .reshape(tgt_shape)
        .astype(np.float32)
    )

    return data


# ============================================================
# DATASET VALIDATION
# ============================================================

def validate_dataset_shapes(data):

    assert (
        data["encoder_x"]
        .shape[1]
        ==
        ENCODER_LEN
    )

    assert (
        data["decoder_x"]
        .shape[1]
        ==
        DECODER_LEN
    )

    assert (
        data["target_y"]
        .shape[1]
        ==
        PRED_LEN
    )

    assert (
        data["target_y"]
        .shape[2]
        ==
        len(TARGET_COLS)
    )

    print(
        "\nDataset Shapes"
    )

    print(
        "encoder_x:",
        data["encoder_x"].shape
    )

    print(
        "decoder_x:",
        data["decoder_x"].shape
    )

    print(
        "target_y:",
        data["target_y"].shape
    )


# ============================================================
# SAVE DATASET
# ============================================================

def save_dataset(
    data,
    output_path,
):

    torch.save(
        {
            "encoder_x":
                torch.tensor(
                    data["encoder_x"],
                    dtype=torch.float32,
                ),

            "decoder_x":
                torch.tensor(
                    data["decoder_x"],
                    dtype=torch.float32,
                ),

            "target_y":
                torch.tensor(
                    data["target_y"],
                    dtype=torch.float32,
                ),

            "product_id":
                torch.tensor(
                    data["product_id"],
                    dtype=torch.long,
                ),

            "category_id":
                torch.tensor(
                    data["category_id"],
                    dtype=torch.long,
                ),

            "trajectory_id":
                data["trajectory_id"],
        },
        output_path,
    )


# ============================================================
# METADATA
# ============================================================

def save_metadata(
    encoder_cols,
    decoder_cols,
    product_vocab,
    category_vocab,
):

    metadata = {

        "encoder_features":
            encoder_cols,

        "decoder_features":
            decoder_cols,

        "target_features":
            TARGET_COLS,

        "encoder_length":
            ENCODER_LEN,

        "decoder_length":
            DECODER_LEN,

        "prediction_length":
            PRED_LEN,

        "num_encoder_features":
            len(
                encoder_cols
            ),

        "num_decoder_features":
            len(
                decoder_cols
            ),

        "num_targets":
            len(
                TARGET_COLS
            ),

        "num_products":
            len(
                product_vocab
            ),

        "num_categories":
            len(
                category_vocab
            ),
    }

    save_json(
        metadata,
        ARTIFACT_DIR /
        "feature_metadata.json",
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "\nLoading CSV..."
    )

    df = pd.read_csv(
        INPUT_FILE
    )

    validate_schema(df)

    validate_nulls(df)

    df[DAY_COL] = pd.to_numeric(
        df[DAY_COL],
        errors="raise",
    )

    df = (
        df
        .sort_values(
            [
                TRAJECTORY_COL,
                DAY_COL,
            ]
        )
        .reset_index(
            drop=True
        )
    )

    validate_trajectories(
        df
    )

    decoder_cols = (
        discover_decoder_features(
            df
        )
    )

    encoder_cols = (
        discover_encoder_features(
            df
        )
    )

    product_vocab = (
        build_vocab(
            df[PRODUCT_COL]
        )
    )

    category_vocab = (
        build_vocab(
            df[CATEGORY_COL]
        )
    )

    df = encode_static_ids(
        df,
        product_vocab,
        category_vocab,
    )

    (
        train_ids,
        val_ids,
        test_ids,
    ) = split_trajectories(
        df
    )

    train_df = df[
        df[
            TRAJECTORY_COL
        ]
        .isin(train_ids)
    ]

    val_df = df[
        df[
            TRAJECTORY_COL
        ]
        .isin(val_ids)
    ]

    test_df = df[
        df[
            TRAJECTORY_COL
        ]
        .isin(test_ids)
    ]

    print(
        "\nBuilding Train Windows..."
    )

    train_samples = (
        build_windows(
            train_df,
            encoder_cols,
            decoder_cols,
        )
    )

    print(
        "\nBuilding Validation Windows..."
    )

    val_samples = (
        build_windows(
            val_df,
            encoder_cols,
            decoder_cols,
        )
    )

    print(
        "\nBuilding Test Windows..."
    )

    test_samples = (
        build_windows(
            test_df,
            encoder_cols,
            decoder_cols,
        )
    )

    train_data = (
        samples_to_arrays(
            train_samples
        )
    )

    val_data = (
        samples_to_arrays(
            val_samples
        )
    )

    test_data = (
        samples_to_arrays(
            test_samples
        )
    )

    (
        encoder_scaler,
        decoder_scaler,
        target_scaler,
    ) = fit_scalers(
        train_data
    )

    train_data = (
        scale_dataset(
            train_data,
            encoder_scaler,
            decoder_scaler,
            target_scaler,
        )
    )

    val_data = (
        scale_dataset(
            val_data,
            encoder_scaler,
            decoder_scaler,
            target_scaler,
        )
    )

    test_data = (
        scale_dataset(
            test_data,
            encoder_scaler,
            decoder_scaler,
            target_scaler,
        )
    )

    validate_dataset_shapes(
        train_data
    )

    validate_dataset_shapes(
        val_data
    )

    validate_dataset_shapes(
        test_data
    )

    save_pickle(
        encoder_scaler,
        ARTIFACT_DIR /
        "encoder_scaler.pkl",
    )

    save_pickle(
        decoder_scaler,
        ARTIFACT_DIR /
        "decoder_scaler.pkl",
    )

    save_pickle(
        target_scaler,
        ARTIFACT_DIR /
        "target_scaler.pkl",
    )

    save_json(
        product_vocab,
        ARTIFACT_DIR /
        "product_vocab.json",
    )

    save_json(
        category_vocab,
        ARTIFACT_DIR /
        "category_vocab.json",
    )

    save_metadata(
        encoder_cols,
        decoder_cols,
        product_vocab,
        category_vocab,
    )

    save_dataset(
        train_data,
        ARTIFACT_DIR /
        "train_dataset.pt",
    )

    save_dataset(
        val_data,
        ARTIFACT_DIR /
        "val_dataset.pt",
    )

    save_dataset(
        test_data,
        ARTIFACT_DIR /
        "test_dataset.pt",
    )

    print("\nDone.")


if __name__ == "__main__":
    main()