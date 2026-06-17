import pandas as pd
from pandas.api.types import (
    is_numeric_dtype,
    is_datetime64_any_dtype,
)

TEMPORAL_COLUMNS = {
    "date",
    "day",
    "days",
    "timestamp",
    "time",
    "event_time",
}



class FeatureTyping:

    def infer_types(
        self,
        df: pd.DataFrame
    ) -> dict:

        types = {}

        for column in df.columns:

            col = df[column]
            col_name = column.lower()

            # Identifier
            if col_name=="id" or col_name.endswith("_id"):
                types[column] = "identifier"
                continue

            # Temporal (actual datetime dtype)
            if is_datetime64_any_dtype(col):
                types[column] = "temporal"
                continue

            # Temporal (name based)
            if (
                col_name in TEMPORAL_COLUMNS
                or col_name.endswith("_date")
                or col_name.endswith("_day")
            ):
                types[column] = "temporal"
                continue

            # Numerical
            if is_numeric_dtype(col):
                types[column] = "numerical"
                continue

            # Categorical
            types[column] = "categorical"

        return types