import pandas as pd
import numpy as np
from scipy.stats import f_oneway

from core.models import Edge


class AnovaDiscovery:

    def anova_discover(
        self,
        df: pd.DataFrame,
        pairs: list,
        feature_types: dict
    ):

        relationships = []

        for col1, col2, pair_type in pairs:

            if pair_type != "cat_num":
                continue

            # Use FeatureTyping output
            if feature_types[col1] == "categorical":

                cat_col = col1
                num_col = col2

            else:

                cat_col = col2
                num_col = col1

            try:

                data = df[
                    [cat_col, num_col]
                ].dropna()

                groups = []

                for _, group in data.groupby(cat_col):

                    values = group[num_col]

                    if len(values) >= 2:

                        groups.append(values)

                if len(groups) < 2:
                    continue

                f_stat, p_value = f_oneway(
                    *groups
                )
                if np.isinf(f_stat):
                  continue

                relationships.append(
                    Edge(
                        node_1=cat_col,
                        node_2=num_col,
                        method="anova",
                        score=float(f_stat),
                        raw_score=float(f_stat),
                        p_value=float(p_value)
                    )
                )

            except Exception as e:

                print(
                    f"ANOVA Error: "
                    f"{col1} | {col2} | {e}"
                )

                continue

        relationships.sort(
            key=lambda x: x.score,
            reverse=True
        )

        return relationships