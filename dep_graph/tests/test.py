import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        ".."
    )
)

sys.path.insert(0, PROJECT_ROOT)

import pandas as pd

from feature_typing.feature_typing import FeatureTyping
from discovery.pair_selector import PairSelector

from discovery.numerical.pearson import PearsonDiscovery
from discovery.numerical.spearman import SpearmanDiscovery

from discovery.categorical.chi_square import ChiSquareDiscovery
from discovery.categorical.cramers import CramersVDiscovery
from discovery.mixed.anova import AnovaDiscovery
from causal.pc_algo import PCDiscovery
from graph.builder import GraphBuilder
from graph.traversal import GraphTraversal
# ----------------------------------
# Load Data
# ----------------------------------

df = pd.read_csv(
    "../../backend/temporal_dataset.csv"
)



# ----------------------------------
# Feature Typing
# ----------------------------------

ft = FeatureTyping()

feature_types = ft.infer_types(
    df
)

print("\nDetected Feature Types:\n")
for feature, ftype in feature_types.items():
    print(f"{feature}: {ftype}")
# ----------------------------------
# Pair Selection
# ----------------------------------

pair_selector = PairSelector()

pairs = pair_selector.generate_pairs(
    feature_types
)
for pair in pairs:
    print(pair)
print(
    f"\nTotal Candidate Pairs: "
    f"{len(pairs)}\n"
)


# ----------------------------------
# Pearson
# ----------------------------------

pearson = PearsonDiscovery()

pearson_relationships = pearson.pearson_discover(
    df,
    pairs
)

print(
    f"\nPearson Relationships: "
    f"{len(pearson_relationships)}\n"
)

for rel in pearson_relationships[:20]:
    print(rel)


# ----------------------------------
# Spearman
# ----------------------------------

spearman = SpearmanDiscovery()

spearman_relationships = spearman.spearman_discover(
    df,
    pairs
)

print(
    f"\nSpearman Relationships: "
    f"{len(spearman_relationships)}\n"
)

for rel in spearman_relationships[:20]:
    print(rel)


# ----------------------------------
# Compare Results
# ----------------------------------

pearson_pairs = {
    tuple(sorted([r.node_1, r.node_2]))
    for r in pearson_relationships
}

spearman_pairs = {
    tuple(sorted([r.node_1, r.node_2]))
    for r in spearman_relationships
}

# Spearman-only discoveries

extra_spearman = spearman_pairs - pearson_pairs

print(
    "\nFound only by Spearman:\n"
)

for pair in sorted(extra_spearman):
    print(pair)
    
    
chi = ChiSquareDiscovery()

chi_relationships = (
    chi.chi_square_discover(
        df,
        pairs
    )
)

print(
    f"\nChi Square Relationships: "
    f"{len(chi_relationships)}\n"
)

for rel in chi_relationships[:20]:
    print(rel)


cramers = CramersVDiscovery()

cramers_relationships = (
    cramers.cramers_v_discover(
        df,
        pairs
    )
)

print(
    f"\nCramers V Relationships: "
    f"{len(cramers_relationships)}\n"
)

for rel in cramers_relationships[:20]:
    print(rel)
    

anova = AnovaDiscovery()

anova_relationships = (
    anova.anova_discover(
        df,
        pairs,
        feature_types
    )
)
print(
    f"\nANOVA Relationships: "
    f"{len(anova_relationships)}\n"
)

for rel in anova_relationships:
    print(rel)
    
# pc = PCDiscovery()

# pc_relationships = pc.discover(
#     df,
#     feature_types
# )

# print(
#     f"\nPC Relationships: "
#     f"{len(pc_relationships)}\n"
# )

# for rel in pc_relationships[:20]:
#     print(rel)
    
# pearson_pairs = {
#     tuple(sorted([r.node_1, r.node_2]))
#     for r in pearson_relationships
# }

# pc_pairs = {
#     tuple(sorted([r.node_1, r.node_2]))
#     for r in pc_relationships
# }
# removed_by_pc = pearson_pairs - pc_pairs

# print(
#     f"\nRemoved By PC: "
#     f"{len(removed_by_pc)}\n"
# )

# for pair in sorted(removed_by_pc):
#     print(pair)
    
# kept_by_pc = pearson_pairs & pc_pairs

# print(
#     f"\nKept By PC: "
#     f"{len(kept_by_pc)}\n"
# )

# for pair in sorted(list(kept_by_pc))[:20]:
#     print(pair)
    
# reduction = (
#     len(removed_by_pc)
#     / len(pearson_pairs)
# ) * 100

# print(
#     f"\nGraph Reduction: "
#     f"{reduction:.2f}%"
# )


from discovery.fusion import FusionEngine
all_edges = (

    pearson_relationships

    + spearman_relationships

    + cramers_relationships

    + anova_relationships
)

fusion = FusionEngine()

fused_edges = fusion.fuse(
    all_edges
)

print(
    f"\nFused Relationships: "
    f"{len(fused_edges)}\n"
)

for edge in fused_edges:
    print(edge)
    
builder = GraphBuilder()

graph = builder.build(
    fused_edges
)
import matplotlib.pyplot as plt
import networkx as nx

plt.figure(figsize=(18, 12))

pos = nx.spring_layout(
    graph,
    seed=42,
    k=1
)

nx.draw_networkx_nodes(
    graph,
    pos,
    node_size=2000
)

nx.draw_networkx_labels(
    graph,
    pos,
    font_size=8
)

nx.draw_networkx_edges(
    graph,
    pos,
    alpha=0.5
)

plt.title("Dependency Graph")

plt.show()

print(
    f"\nNodes: {graph.number_of_nodes()}"
)

print(
    f"Edges: {graph.number_of_edges()}"
)
print("\nSample Edges:\n")

traversal = GraphTraversal()

print("\n")
print("=" * 50)
print("SHIPPING FEE KPI IMPACTS")
print("=" * 50)




for node in graph.nodes():

    print("\n")
    print("=" * 50)
    print(node)
    print("=" * 50)

    results = traversal.get_impacted_nodes(
        graph,
        node
    )
    
    for r in results:
        print(r)


input_metric = "shipping_fee"

impacted = traversal.get_impacted_nodes(
    graph,
    input_metric
)

print("\nINPUT:")
print(input_metric)

print("\nIMPACTED:")
for x in impacted:
    print(x)