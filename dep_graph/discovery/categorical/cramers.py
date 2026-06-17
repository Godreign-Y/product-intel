import numpy as np
import pandas as pd

from scipy.stats import chi2_contingency

from core.models import Edge


class CramersVDiscovery:

    def cramers_v_discover(
        self,
        df: pd.DataFrame,
        pairs: list,
        min_score: float = 0.1
    ):

        relationships = []

        for col1, col2, pair_type in pairs:

            if pair_type != "cat_cat":
                continue

            try:

                table = pd.crosstab(
                    df[col1],
                    df[col2]
                )

                if table.empty:
                    continue

                chi2, p_value, _, _ = (
                    chi2_contingency(table)
                )

                n = table.values.sum()

                r, c = table.shape

                denom = min(
                    r - 1,
                    c - 1
                )

                if denom <= 0:
                    continue

                v = np.sqrt(
                    chi2 /
                    (
                        n * denom
                    )
                )

                if v < min_score:
                    continue

                relationships.append(
                    Edge(
                        node_1=col1,
                        node_2=col2,
                        method="cramers_v",
                        score=float(v),
                        raw_score=float(v),
                        p_value=float(p_value)
                    )
                )

            except Exception:
                continue

        relationships.sort(
            key=lambda x: x.score,
            reverse=True
        )

        return relationships