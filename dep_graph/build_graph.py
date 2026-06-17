import joblib
import pandas as pd

from feature_typing.feature_typing import FeatureTyping
from discovery.pair_selector import PairSelector

from discovery.numerical.pearson import PearsonDiscovery
from discovery.numerical.spearman import SpearmanDiscovery

from discovery.categorical.chi_square import ChiSquareDiscovery
from discovery.categorical.cramers import CramersVDiscovery

from discovery.mixed.anova import AnovaDiscovery

from discovery.fusion import FusionEngine
from graph.builder import GraphBuilder


def build_dependency_graph(csv_path):

    df = pd.read_csv(csv_path)

    ft = FeatureTyping()

    feature_types = ft.infer_types(df)

    pair_selector = PairSelector()

    pairs = pair_selector.generate_pairs(
        feature_types
    )

    pearson_relationships = (
        PearsonDiscovery().pearson_discover(
            df,
            pairs
        )
    )

    spearman_relationships = (
        SpearmanDiscovery().spearman_discover(
            df,
            pairs
        )
    )

    chi_relationships = (
        ChiSquareDiscovery().chi_square_discover(
            df,
            pairs
        )
    )

    cramers_relationships = (
        CramersVDiscovery().cramers_v_discover(
            df,
            pairs
        )
    )

    anova_relationships = (
        AnovaDiscovery().anova_discover(
            df,
            pairs,
            feature_types
        )
    )

    all_edges = (
        pearson_relationships
        + spearman_relationships
        + chi_relationships
        + cramers_relationships
        + anova_relationships
    )

    fused_edges = (
        FusionEngine().fuse(all_edges)
    )

    graph = (
        GraphBuilder().build(fused_edges)
    )

    return graph


if __name__ == "__main__":

    graph = build_dependency_graph(
        "../backend/temporal_dataset.csv"
    )
    
    joblib.dump(
        graph,
        "dependency_graph.pkl"
    )

    print(
        f"Saved graph with "
        f"{graph.number_of_nodes()} nodes and "
        f"{graph.number_of_edges()} edges"
    )