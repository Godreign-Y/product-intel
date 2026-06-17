import networkx as nx


class GraphBuilder:

    def build(
        self,
        edges
    ):

        graph = nx.Graph()

        for edge in edges:

            graph.add_edge(
                edge.node_1,
                edge.node_2,

                score=edge.score,

                method=edge.method,

                evidence=edge.evidence
            )

        return graph