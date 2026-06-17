import os
import joblib


def load_dependency_graph():

    current_dir = os.path.dirname(__file__)

    graph_path = os.path.join(
        current_dir,
        "dependency_graph.pkl"
    )

    graph = joblib.load(
        graph_path
    )

    return graph