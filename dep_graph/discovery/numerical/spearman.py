from scipy.stats import spearmanr

import pandas as pd
from core.models import Edge

class SpearmanDiscovery:

    def spearman_discover(
        self,
        df: pd.DataFrame,
        pairs: list,
        min_corr: float = 0.3,
        max_p_value: float = 0.05
    ):

        relationships = []

        for col1, col2, pair_type in pairs:

            if pair_type != "num_num":
                continue

            data = df[[col1, col2]].dropna()

            if len(data) < 3:
                continue

            try:

                corr, p_value = spearmanr(
                    data[col1],
                    data[col2]
                )

                if abs(corr) < min_corr:
                    continue

                if p_value > max_p_value:
                    continue

                relationships.append(
                   Edge(
                        node_1=col1,    
                        node_2=col2,
                        method="spearman",
                        score=float(abs(corr)),
                        raw_score=float(corr), 
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