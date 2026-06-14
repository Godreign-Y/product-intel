import os
import joblib
import json
import pandas as pd
import numpy as np
import warnings
from typing import Tuple, Dict, List

warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)

class TimeSeriesPreprocessor:
    def __init__(self, target_cols: List[str] = None, lag_days: List[int] = None, rolling_windows: List[int] = None):
        self.target_cols = target_cols or ["revenue", "profit", "orders", "conversion_rate", "retention_rate"]
        self.lag_days = lag_days or [1, 7, 14, 30]
        self.rolling_windows = rolling_windows or [7, 14, 30]
        self.categorical_cols = ["product_id", "category"]
        self.feature_cols: List[str] = []
        self.cat_mappings: Dict[str, Dict[str, int]] = {}
        
    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.sort_values(by=["product_id", "date"]).reset_index(drop=True)
        df["date"] = pd.to_datetime(df["date"])
        
        for col in self.categorical_cols:
            unique_vals = sorted(df[col].unique())
            mapping = {val: idx for idx, val in enumerate(unique_vals)}
            self.cat_mappings[col] = mapping
            
        return self._transform_internal(df, is_training=True)
        
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.sort_values(by=["product_id", "date"]).reset_index(drop=True)
        df["date"] = pd.to_datetime(df["date"])
        return self._transform_internal(df, is_training=False)
        
    def _transform_internal(self, df: pd.DataFrame, is_training: bool = False) -> pd.DataFrame:
        new_cols = {}
        
        # 1. Date Features
        new_cols["day_of_week"] = df["date"].dt.dayofweek
        new_cols["month"] = df["date"].dt.month
        new_cols["quarter"] = df["date"].dt.quarter
        new_cols["is_weekend"] = (new_cols["day_of_week"] >= 5).astype(int)
        
        for col in self.categorical_cols:
            mapping = self.cat_mappings[col]
            new_cols[col + "_code"] = df[col].map(mapping).fillna(-1).astype(int)
            
        # 2. Lag Features (1, 7, 14, 30) & 3. Rolling Features
        lag_vars = self.target_cols + ["marketing_spend", "avg_selling_price", "discount_pct", "shipping_fee", "current_ctr", "current_roas", "traffic"]
        
        # Check if we have a single product (very common during recursive forecasting)
        unique_products = df["product_id"].unique()
        is_single_product = len(unique_products) == 1
        
        if is_single_product:
            # Bypass groupby for 100x speedup
            for col in lag_vars:
                for lag in self.lag_days:
                    new_cols[f"{col}_lag_{lag}"] = df[col].shift(lag)
            
            for col in self.target_cols + ["current_ctr", "current_roas", "traffic"]:
                lagged_col = df[col].shift(1)
                for win in self.rolling_windows:
                    r = lagged_col.rolling(win, min_periods=1)
                    new_cols[f"{col}_roll_mean_{win}"] = r.mean()
                    new_cols[f"{col}_roll_std_{win}"] = r.std().fillna(0.0)
                    new_cols[f"{col}_roll_max_{win}"] = r.max()
                    new_cols[f"{col}_roll_min_{win}"] = r.min()
        else:
            grouped = df.groupby("product_id")
            for col in lag_vars:
                grouped_col = grouped[col]
                for lag in self.lag_days:
                    new_cols[f"{col}_lag_{lag}"] = grouped_col.shift(lag)
            
            for col in self.target_cols + ["current_ctr", "current_roas", "traffic"]:
                lagged_col = grouped[col].shift(1)
                lagged_grouped = lagged_col.groupby(df["product_id"])
                for win in self.rolling_windows:
                    new_cols[f"{col}_roll_mean_{win}"] = lagged_grouped.transform(lambda x: x.rolling(win, min_periods=1).mean())
                    new_cols[f"{col}_roll_std_{win}"] = lagged_grouped.transform(lambda x: x.rolling(win, min_periods=1).std()).fillna(0.0)
                    new_cols[f"{col}_roll_max_{win}"] = lagged_grouped.transform(lambda x: x.rolling(win, min_periods=1).max())
                    new_cols[f"{col}_roll_min_{win}"] = lagged_grouped.transform(lambda x: x.rolling(win, min_periods=1).min())

        # 4. Marketing Features (CTR, ROAS, Traffic Trends: 7d mean / 30d mean)
        new_cols["ctr_trend"] = (new_cols["current_ctr_roll_mean_7"] + 1e-5) / (new_cols["current_ctr_roll_mean_30"] + 1e-5)
        new_cols["roas_trend"] = (new_cols["current_roas_roll_mean_7"] + 1e-5) / (new_cols["current_roas_roll_mean_30"] + 1e-5)
        new_cols["traffic_trend"] = (new_cols["traffic_roll_mean_7"] + 1e-5) / (new_cols["traffic_roll_mean_30"] + 1e-5)

        # 5. Inventory Features
        new_cols["inventory_ratio"] = df["inventory_available"] / (df["traffic"] + 1e-5)
        new_cols["stock_days"] = df["inventory_available"] / (new_cols["orders_roll_mean_7"] + 1.0)

        # 6. Price Features
        new_cols["discount_buckets"] = np.where(
            df["discount_pct"] <= 10.0, 0,
            np.where(df["discount_pct"] <= 20.0, 1,
                     np.where(df["discount_pct"] <= 30.0, 2, 3))
        )
        
        if is_single_product:
            category_mean_price = df["avg_selling_price"]
        else:
            category_mean_price = df.groupby(["category", "date"])["avg_selling_price"].transform("mean")
        new_cols["price_index"] = df["avg_selling_price"] / (category_mean_price + 1e-5)

        # 7. Growth Features (lag 1 vs lag 7 rate of change)
        new_cols["revenue_growth"] = (new_cols["revenue_lag_1"] - new_cols["revenue_lag_7"]) / (new_cols["revenue_lag_7"] + 1e-5)
        new_cols["order_growth"] = (new_cols["orders_lag_1"] - new_cols["orders_lag_7"]) / (new_cols["order_growth" if "order_growth" in new_cols else "orders_lag_7"] + 1e-5)
        # Note: fixing order_growth and marketing_growth formula to use the correct denominator
        new_cols["order_growth"] = (new_cols["orders_lag_1"] - new_cols["orders_lag_7"]) / (new_cols["orders_lag_7"] + 1e-5)
        new_cols["marketing_growth"] = (new_cols["marketing_spend_lag_1"] - new_cols["marketing_spend_lag_7"]) / (new_cols["marketing_spend_lag_7"] + 1e-5)

        # Concat all features at once to prevent fragmentation
        processed_df = pd.concat([df, pd.DataFrame(new_cols, index=df.index)], axis=1)

        if is_training:
            processed_df = processed_df.dropna().reset_index(drop=True)
            
            # Determine final list of features
            exclude_cols = [
                "date", "product_id", "category", "subcategory", "brand", 
                "sales_channel_mix", "campaign_mix", "acquisition_mix",
                "dominant_age_group"
            ] + self.target_cols
            
            candidate_features = [c for c in processed_df.columns if c not in exclude_cols]
            
            self.feature_cols = [
                c for c in candidate_features 
                if pd.api.types.is_numeric_dtype(processed_df[c])
            ]
            
        return processed_df

    def split_data(self, df: pd.DataFrame, train_end: str = "2025-06-30", val_end: str = "2025-09-30") -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        df["date_str"] = df["date"].dt.strftime("%Y-%m-%d")
        train_df = df[df["date_str"] <= train_end].drop(columns=["date_str"])
        val_df = df[(df["date_str"] > train_end) & (df["date_str"] <= val_end)].drop(columns=["date_str"])
        test_df = df[df["date_str"] > val_end].drop(columns=["date_str"])
        return train_df, val_df, test_df

    def save(self, filepath: str):
        joblib.dump({
            "target_cols": self.target_cols,
            "lag_days": self.lag_days,
            "rolling_windows": self.rolling_windows,
            "categorical_cols": self.categorical_cols,
            "feature_cols": self.feature_cols,
            "cat_mappings": self.cat_mappings
        }, filepath)
        
    @classmethod
    def load(cls, filepath: str) -> "TimeSeriesPreprocessor":
        data = joblib.load(filepath)
        preprocessor = cls(
            target_cols=data["target_cols"],
            lag_days=data["lag_days"],
            rolling_windows=data["rolling_windows"]
        )
        preprocessor.categorical_cols = data["categorical_cols"]
        preprocessor.feature_cols = data["feature_cols"]
        preprocessor.cat_mappings = data["cat_mappings"]
        return preprocessor
