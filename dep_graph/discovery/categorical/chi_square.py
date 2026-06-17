import pandas as pd

from scipy.stats import chi2_contingency

from core.models import Edge


class ChiSquareDiscovery:

    def chi_square_discover(
        self,
        df: pd.DataFrame,
        pairs: list,
        max_p_value: float = 0.05
    ):

        relationships = []

        for col1, col2, pair_type in pairs:

            if pair_type != "cat_cat":
                continue

            try:

                contingency_table = pd.crosstab(
                    df[col1],
                    df[col2]
                )

                if contingency_table.empty:
                    continue

                chi2, p_value, _, _ = (
                    chi2_contingency(
                        contingency_table
                    )
                )

                if p_value > max_p_value:
                    continue

                relationships.append(
                    Edge(
                        node_1=col1,
                        node_2=col2,
                        method="chi_square",
                        score=float(chi2),
                        raw_score=float(chi2),
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