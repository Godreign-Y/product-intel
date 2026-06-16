"""
Trajectory simulator orchestrates full generation.
"""
from typing import Dict, Any, List
from simulator.core.models import BusinessState, SimulationConfig
from simulator.core.state_transition import StateTransitionEngine

class AnchorStateResolver:
    """Resolves the initial state based on the anchor day."""
    
    def resolve(self, product: Dict[str, Any], anchor_day: int) -> BusinessState:
        """
        Return the state at the given anchor day.
        For POC, we just return the product's base state.
        """
        base = product.get("base_state", {})
        state = BusinessState(
            inventory_available=int(base.get("inventory_available", 1000)),
            avg_selling_price=float(base.get("avg_selling_price", 100.0)),
            effective_price=float(base.get("avg_selling_price", 100.0)),
            discount_pct=float(base.get("discount_pct", 0.0)),
            shipping_fee=float(base.get("shipping_fee", 0.0)),
            marketing_spend=float(base.get("marketing_spend", 50.0)),
            sales_channel_mix=base.get("sales_channel_mix", {}),
            campaign_mix=base.get("campaign_mix", {}),
            acquisition_mix=base.get("acquisition_mix", {}),
            traffic=int(base.get("traffic", 500)),
            active_users=int(base.get("active_users", 200)),
            current_ctr=float(base.get("current_ctr", 0.05)),
            current_roas=float(base.get("current_roas", 2.0)),
            orders=int(base.get("orders", 10)),
            fulfilled_orders=int(base.get("orders", 10)),
            revenue=float(base.get("revenue", 1000.0)),
            profit=float(base.get("profit", 200.0)),
            conversion_rate=float(base.get("conversion_rate", 0.05)),
            retention_rate=float(base.get("retention_rate", 0.2)),
            avg_ltv=float(base.get("avg_ltv", 500.0))
        )
        return state

class BaselineTrajectoryGenerator:
    """Generates natural trajectory without interventions."""
    
    def __init__(self, transition_engine: StateTransitionEngine):
        self.transition_engine = transition_engine

    def generate(self, initial_state: BusinessState, config: SimulationConfig, inventory_policy: str) -> List[BusinessState]:
        import copy
        trajectory = []
        persistent_state = copy.deepcopy(initial_state)
        for day in range(config.simulation_days):
            persistent_state, day_state = self.transition_engine.transition(
                persistent_state, [], day, config.noise_enabled, inventory_policy, trajectory
            )
            trajectory.append(day_state)
        return trajectory

class ActionEngine:
    """Filters actions to those currently active."""
    
    @staticmethod
    def get_active_actions(schedule: List[Dict[str, Any]], current_day: int) -> List[Dict[str, Any]]:
        active = []
        for event in schedule:
            start = event.get("relative_day", 0)
            duration = event.get("duration_days", 1)
            if start <= current_day <= start + duration:
                active.append(event)
        return active

class TrajectorySimulator:
    """Simulates trajectories under interventions."""
    
    def __init__(self, transition_engine: StateTransitionEngine):
        self.transition_engine = transition_engine

    def simulate(self, initial_state: BusinessState, schedule: List[Dict[str, Any]], config: SimulationConfig, inventory_policy: str) -> List[BusinessState]:
        import copy
        trajectory = []
        persistent_state = copy.deepcopy(initial_state)
        
        for day in range(config.simulation_days):
            active_actions = ActionEngine.get_active_actions(schedule, day)
            
            # Step 1: Transition the persistent state based on persistent actions and organic evolution
            persistent_state, day_state = self.transition_engine.transition(
                persistent_state, active_actions, day, config.noise_enabled, inventory_policy, trajectory
            )
            
            trajectory.append(day_state)
            
        return trajectory
