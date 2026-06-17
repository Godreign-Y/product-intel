# Dependency Graph Engine Usage Guide

This guide explains how to use the Dependency Graph Engine to build, load, and traverse dependency graphs from tabular datasets.

## 1. Building the Graph

To build a dependency graph, you need a tabular dataset (CSV format). The engine will automatically type the features, discover statistical relationships, fuse the scores, and build a NetworkX graph.

You can use the `build_dependency_graph` function provided in `build_graph.py`.

```python
from build_graph import build_dependency_graph
import joblib

# 1. Provide the path to your dataset
csv_path = "path/to/your/dataset.csv"

# 2. Build the graph
graph = build_dependency_graph(csv_path)

# 3. Save the generated graph for later use
joblib.dump(graph, "dependency_graph.pkl")

print(f"Graph built with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges.")
```

*Note: Running `python build_graph.py` directly will execute the graph generation on a hardcoded dataset path and output `dependency_graph.pkl` in the current directory.*

## 2. Loading the Graph

Once a graph is generated and saved as a `.pkl` file, you can load it into your runtime environment without needing to rebuild it. The `load_graph.py` module provides a utility for this.

```python
from load_graph import load_dependency_graph

# Loads 'dependency_graph.pkl' from the same directory
graph = load_dependency_graph()

print("Graph loaded successfully.")
```

## 3. Traversing the Graph

The generated graph is a NetworkX Directed Graph. You can use standard NetworkX methods or the provided `GraphTraversal` class to query the graph. The traversal class is specifically designed to find impacted target KPIs downstream of a given source variable.

```python
from graph.traversal import GraphTraversal
from load_graph import load_dependency_graph

# 1. Load the graph
graph = load_dependency_graph()

# 2. Initialize traversal engine
traversal = GraphTraversal()

# 3. Query impacted KPIs for a specific source node (e.g., if 'price' changes)
# The `get_impacted_nodes` method filters for predefined target KPIs and returns
# nodes that meet the minimum confidence score.
impacted_kpis = traversal.get_impacted_nodes(
    graph=graph,
    source_node="price",  # The variable you are simulating a change for
    top_k=5,              # Maximum number of impacted KPIs to return
    min_score=0.30        # Minimum confidence score (0 to 1) for the edge
)

for kpi in impacted_kpis:
    print(f"Impacted KPI: {kpi['node']} (Confidence Score: {kpi['score']:.2f})")
```

### Predefined Target KPIs
The `GraphTraversal` class currently filters for the following predefined target KPIs:
- `revenue`
- `profit`
- `orders`
- `traffic`
- `active_users`
- `conversion_rate`
- `retention_rate`
- `avg_ltv`
- `current_ctr`
- `current_roas`

If you need to query impacts on variables outside of this list, you can either modify `GraphTraversal.TARGET_KPIS` or use standard `networkx.neighbors(graph, source_node)`.
