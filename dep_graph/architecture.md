# Dependency Graph Engine Architecture

This document outlines the architectural design and current implementation of the Dependency Graph Engine. It serves as a guide to understanding the system's pipeline, core components, directory structure, and future roadmap.

## 1. System Overview

The Dependency Graph Engine is a reusable, dataset-agnostic Python library designed to automatically discover statistical relationships between variables in a tabular dataset and construct a dependency graph.

This graph acts as an explainability and impact propagation layer, enabling the system to:
* Identify which variables are statistically linked.
* Enable graph traversal to determine downstream impacts of a variable change.
* Serve as a foundation for what-if analysis and simulation.

## 2. Directory Structure

A standard architectural best practice is to modularize the codebase based on domain responsibilities. The current implementation is organized as follows:

* `core/`: Contains shared data models and domain schemas used across the system (e.g., `models.py`).
* `feature_typing/`: Responsible for automatically classifying dataset columns into appropriate data types (numerical, categorical, datetime, identifier).
* `discovery/`: Contains the statistical engines to identify relationships between pairs of variables.
  * `numerical/`: Implementations for Pearson and Spearman correlation.
  * `categorical/`: Implementations for Chi-Square and Cramer's V tests.
  * `mixed/`: Implementations for mixed data types (e.g., ANOVA).
  * `pair_selector.py`: Generates valid variable pairs for testing based on their inferred feature types.
  * `fusion.py`: Combines and normalizes scores from various statistical tests into unified edge weights.
* `graph/`: Handles the construction and traversal of the final dependency graph.
  * `builder.py`: Constructs a `NetworkX` Directed Graph (DiGraph) from the fused edges.
  * `traversal.py`: Provides APIs to query downstream impacts in the constructed graph.
* `build_graph.py`: The main entry point that orchestrates the pipeline from a CSV to a serialized `dependency_graph.pkl`.
* `load_graph.py`: Utility to load the generated graph artifact.

## 3. High-Level Data Flow (Pipeline)

The engine processes tabular data in a sequence of well-defined steps:

1. **Dataset Ingestion**: Data is loaded (e.g., via `pandas` in `build_graph.py`).
2. **Feature Typing**: The `FeatureTyping` module infers whether each column is Numerical, Categorical, etc.
3. **Pair Generation**: The `PairSelector` creates pairs of variables to be tested for relationships.
4. **Statistical Discovery**: Evaluates pairs using various statistical methods:
   * **Pearson & Spearman** for Numerical ↔ Numerical
   * **Chi-Square & Cramer's V** for Categorical ↔ Categorical
   * **ANOVA** for Categorical ↔ Numerical
5. **Graph Fusion**: The `FusionEngine` aggregates the results from all statistical tests and assigns a normalized confidence score to each relationship edge.
6. **Graph Construction**: `GraphBuilder` builds the `NetworkX` graph.
7. **Graph Serialization**: The graph is exported (`joblib`) for runtime usage.

## 4. Current Implementation Status

As of the current phase, the following components are fully implemented and functional within the codebase:

* **Feature Typing Engine**: Automatically handles classification of raw tabular data.
* **Statistical Discovery Modules**: Standard correlation and association tests are fully integrated.
* **Fusion Engine**: Successfully combines statistical evidence into a singular edge list.
* **Graph Builder & Traversal API**: Graph generation and downstream path traversal using `NetworkX`.

## 5. Future Enhancements (Roadmap)

To reach the full architectural vision (e.g., integration into a larger Product Intelligence Platform), the following features are planned but not yet implemented:

* **Causal Discovery Engine (e.g., PC Algorithm)**: To infer true directional dependencies (cause-and-effect) rather than just bidirectional statistical correlations.
* **Graph Pruning**: Logic to remove noisy, weak relationships or isolated nodes, ensuring a cleaner, more explainable graph.
* **Mutual Information**: To capture more complex, non-linear statistical relationships.
* **Simulation Layer Integration**: Connecting the dependency graph output to Temporal Fusion Transformers (TFT) for time-series forecasting and scenario simulation.
* **LLM Integration**: Enabling natural language querying (e.g., *"What happens if price decreases by 5%?"*) by parsing intent, traversing the graph, and generating business explanations.
