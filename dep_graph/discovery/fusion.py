from collections import defaultdict

import numpy as np

from core.models import Edge


class FusionEngine:

    def fuse(
        self,
        all_edges: list
    ):

        # -------------------------
        # Normalize ANOVA
        # -------------------------

        anova_edges = [

            edge

            for edge in all_edges

            if edge.method == "anova"
        ]

        if anova_edges:

            max_anova = max(
                edge.score
                for edge in anova_edges
            )

            for edge in anova_edges:

                edge.score = (
                    np.log1p(edge.score)
                    /
                    np.log1p(max_anova)
                )

        # -------------------------
        # Group by node pair
        # -------------------------

        grouped = defaultdict(list)

        for edge in all_edges:

            key = tuple(
                sorted(
                    [
                        edge.node_1,
                        edge.node_2
                    ]
                )
            )

            grouped[key].append(edge)

        # -------------------------
        # Fuse
        # -------------------------

        fused_edges = []

        for key, edges in grouped.items():

            scores = [
                edge.score
                for edge in edges
            ]

            methods = [
                edge.method
                for edge in edges
            ]

            final_score = (
                sum(scores)
                / len(scores)
            )

            fused_edges.append(

                Edge(

                    node_1=key[0],

                    node_2=key[1],

                    method="fused",

                    score=float(final_score),

                    evidence=methods
                )

            )

        # -------------------------
        # Sort
        # -------------------------

        fused_edges.sort(
            key=lambda x: x.score,
            reverse=True
        )

        return fused_edges