"""
Market propagation using topological sort and differential elasticity.
"""
import networkx as nx
from typing import Dict, Any, List

class MarketPropagationEngine:
    """
    Executes the causal dependency graph in topological order to propagate market effects.
    """
    def __init__(self, market_graph: Dict[str, List[str]], elasticities: Dict[str, Dict[str, float]]):
        """
        Initialize the MarketPropagationEngine.
        
        Args:
            market_graph: Adjacency list representation of the market state dependency graph.
            elasticities: The edge weights defining elasticity multipliers.
        """
        self.market_graph = market_graph
        self.elasticities = elasticities
        self.dag = nx.DiGraph(market_graph)
        try:
            self.execution_order = list(nx.topological_sort(self.dag))
        except nx.NetworkXUnfeasible:
            self.execution_order = list(market_graph.keys())

    def propagate(self, current_state: Any, prev_state: Any) -> Any:
        """
        Propagate differential effects through the market state.
        
        Args:
            current_state (BusinessState): The day_state to update.
            prev_state (BusinessState): The persistent_state or previous day's state used as a baseline.
            
        Returns:
            BusinessState: The updated state after propagation.
        """
        for node in self.execution_order:
            # We don't need to propagate anything if this node has no outbound edges
            if node not in self.market_graph:
                continue
                
            # If the source node changed, apply the % change to its targets
            if hasattr(current_state, node) and hasattr(prev_state, node):
                cur_val = getattr(current_state, node)
                prev_val = getattr(prev_state, node)
                
                # We skip lists/dicts for now (mixes shouldn't be topological sources in this simple DAG)
                if isinstance(prev_val, (int, float)) and prev_val != 0:
                    pct_change = (cur_val - prev_val) / prev_val
                    
                    if pct_change != 0:
                        for target in self.market_graph[node]:
                            if hasattr(current_state, target):
                                # Get the elasticity
                                target_elasticities = self.elasticities.get(node, {})
                                elasticity = target_elasticities.get(target, 0.0)
                                
                                if elasticity != 0.0:
                                    cur_target_val = getattr(current_state, target)
                                    new_target_val = cur_target_val * (1 + (pct_change * elasticity))
                                    
                                    if isinstance(cur_target_val, int):
                                        setattr(current_state, target, int(new_target_val))
                                    else:
                                        setattr(current_state, target, float(new_target_val))
                                        
        return current_state
