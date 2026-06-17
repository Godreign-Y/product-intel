class GraphTraversal:

    TARGET_KPIS = {
        "revenue",
        "profit",
        "orders",
        "traffic",
        "active_users",
        "conversion_rate",
        "retention_rate",
        "avg_ltv",
        "current_ctr",
        "current_roas"
    }

    def get_impacted_nodes(
        self,
        graph,
        source_node,
        top_k=5,
        min_score=0.30
    ):

        if source_node not in graph:
            return []

        impacted = []

        for neighbor in graph.neighbors(source_node):

            if neighbor not in self.TARGET_KPIS:
                continue

            if neighbor == source_node:
                continue

            score = graph[source_node][neighbor]["score"]

            if score < min_score:
                continue
            

            impacted.append(
                {
                    "node": neighbor,
                    "score": score
                }
            )

        impacted.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        return impacted[:top_k]