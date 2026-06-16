"""
State transition engine mapping Day T to Day T+1.
"""
import copy
from typing import Dict, Any, List, Tuple

from simulator.core.models import BusinessState
from simulator.physics.curves import CurveEngine
from simulator.physics.interactions import InteractionEngine
from simulator.physics.propagation import MarketPropagationEngine

class MixNormalizer:
    """Normalizes mix dictionaries to sum to 100."""
    
    @staticmethod
    def normalize(mix: Dict[str, float]) -> Dict[str, float]:
        total = sum(mix.values())
        if total == 0:
            return mix
        return {k: v / total * 100 for k, v in mix.items()}

class DerivedMetricsEngine:
    """Computes derived metrics based on fundamental states."""
    
    @staticmethod
    def compute(state: BusinessState) -> BusinessState:
        # 0. Active Users (emergent from traffic + retention)
        # Assuming 80% of active users are retained and traffic*ctr brings new ones
        state.active_users = int(max(0, (state.traffic * state.current_ctr) + (state.active_users * 0.8)))
        
        # 1. Orders (emergent from active_users * conversion)
        state.orders = int(max(0, state.active_users * state.conversion_rate))
        
        # 2. Fulfilled Orders (constrained by inventory)
        state.fulfilled_orders = min(state.orders, state.inventory_available)
        
        # 3. Effective Price
        state.effective_price = state.avg_selling_price * (1 - (state.discount_pct / 100))
        
        # 4. Revenue
        state.revenue = state.fulfilled_orders * state.effective_price
        
        # 5. Profit
        margin = max(0.0, 0.4 - (state.discount_pct / 100))
        state.profit = state.revenue * margin - state.marketing_spend
        
        # 6. ROAS
        if state.marketing_spend > 0:
            state.current_roas = (state.revenue * 0.3) / state.marketing_spend
        else:
            state.current_roas = 0.0
            
        return state

class StateTransitionEngine:
    """Pipelines all physics to step state forward."""
    
    def __init__(self, 
                 curve_engine: CurveEngine,
                 interaction_engine: InteractionEngine,
                 propagation_engine: MarketPropagationEngine,
                 elasticities: Dict[str, Any],
                 archetypes: Dict[str, Any],
                 assumptions: Dict[str, Any]):
        self.curve_engine = curve_engine
        self.interaction_engine = interaction_engine
        self.propagation_engine = propagation_engine
        self.elasticities = elasticities
        self.archetypes = archetypes
        self.assumptions = assumptions

    def _replenish_inventory(self, state: BusinessState, day: int, policy: str, trajectory: List[BusinessState]):
        if policy == "daily":
            state.inventory_available += 500
        elif policy == "weekly" and day % 7 == 0:
            state.inventory_available += 3500
        elif policy == "monthly" and day % 30 == 0:
            state.inventory_available += 15000
        elif policy == "dynamic":
            if day > 0 and len(trajectory) >= 7:
                recent_orders = [s.fulfilled_orders for s in trajectory[-7:]]
                avg = sum(recent_orders) / 7
                cov = self.assumptions.get("dynamic_inventory_coverage_days", 14)
                target = int(avg * cov)
                if state.inventory_available < target:
                    state.inventory_available = target
            else:
                if day % 7 == 0:
                    state.inventory_available += 2000

    def _apply_effect(self, state: BusinessState, feature: str, op: str, delta: float, action: Dict[str, Any]):
        if op == "mix_shift":
            source = action.get("source")
            target = action.get("target")
            if hasattr(state, feature):
                mix = getattr(state, feature)
                if source in mix and target in mix:
                    actual_delta = min(delta, mix[source])
                    mix[source] -= actual_delta
                    mix[target] += actual_delta
        elif op == "relative_pct":
            if hasattr(state, feature):
                val = getattr(state, feature)
                if feature in ["discount_pct", "shipping_fee"] or val == 0:
                    # Fallback to absolute point addition if relative pct doesn't make sense or val is 0
                    setattr(state, feature, max(0.0, float(val + delta)))
                else:
                    if isinstance(val, int):
                        setattr(state, feature, int(val * (1 + delta/100)))
                    else:
                        setattr(state, feature, float(val * (1 + delta/100)))

    def transition(self, persistent_state: BusinessState, active_actions: List[Dict[str, Any]], day: int, noise_enabled: bool, inventory_policy: str, trajectory: List[BusinessState]) -> Tuple[BusinessState, BusinessState]:
        day_state = copy.deepcopy(persistent_state)
        
        # 1. Replenishment
        self._replenish_inventory(persistent_state, day, inventory_policy, trajectory)
        day_state.inventory_available = persistent_state.inventory_available
        
        # 2. Apply Actions
        pers_rules = self.assumptions.get("persistence_rules", {})
        for action in active_actions:
            feature = action.get("feature")
            delta = action.get("delta", 0.0)
            op = action.get("operation", "relative_pct")
            
            is_persistent = pers_rules.get(feature, False)
            
            if is_persistent:
                if action.get("relative_day") == day:
                    self._apply_effect(persistent_state, feature, op, delta, action)
                    self._apply_effect(day_state, feature, op, delta, action)
            else:
                # Temporary effects applied only to day_state
                profile = "immediate"
                multiplier = self.curve_engine.compute_multiplier(profile, day - action.get("relative_day", day))
                self._apply_effect(day_state, feature, op, delta * multiplier, action)
                
        # 3. Normalize Mixes
        day_state.sales_channel_mix = MixNormalizer.normalize(day_state.sales_channel_mix)
        day_state.campaign_mix = MixNormalizer.normalize(day_state.campaign_mix)
        day_state.acquisition_mix = MixNormalizer.normalize(day_state.acquisition_mix)
        persistent_state.sales_channel_mix = MixNormalizer.normalize(persistent_state.sales_channel_mix)
        persistent_state.campaign_mix = MixNormalizer.normalize(persistent_state.campaign_mix)
        persistent_state.acquisition_mix = MixNormalizer.normalize(persistent_state.acquisition_mix)
        
        # 4. Market Propagation
        prev_state = trajectory[-1] if trajectory else persistent_state
        day_state = self.propagation_engine.propagate(day_state, prev_state)
        
        # 5. Derived Metrics
        day_state = DerivedMetricsEngine.compute(day_state)
        
        # 6. Inventory Depletion
        persistent_state.inventory_available -= day_state.fulfilled_orders
        if persistent_state.inventory_available < 0:
            persistent_state.inventory_available = 0
            
        # 7. Retention Memory (EMA towards baseline to prevent decay to 0)
        decay = self.assumptions.get("retention_decay", 0.95)
        baseline_ret = trajectory[0].retention_rate if trajectory else persistent_state.retention_rate
        
        influences = day_state.retention_rate - persistent_state.retention_rate
        new_retention = (persistent_state.retention_rate * decay) + (baseline_ret * (1 - decay)) + influences
        day_state.retention_rate = max(0.0, min(1.0, new_retention))
        persistent_state.retention_rate = day_state.retention_rate
        
        # 8. LTV Memory
        alpha = self.assumptions.get("ltv_update_alpha", 0.1)
        beta = self.assumptions.get("ltv_update_beta", 0.05)
        
        ret_change = day_state.retention_rate - (trajectory[-1].retention_rate if trajectory else persistent_state.retention_rate)
        rev_change = day_state.revenue - (trajectory[-1].revenue if trajectory else persistent_state.revenue)
        
        new_ltv = persistent_state.avg_ltv + (alpha * ret_change * 1000) + (beta * rev_change)
        day_state.avg_ltv = max(0.01, new_ltv)
        persistent_state.avg_ltv = day_state.avg_ltv

        # 9. Noise & Volatility
        if noise_enabled:
            import random
            
            # Shared volume noise preserves strong correlation between traffic, users, and orders
            volume_noise = random.gauss(1.0, 0.03)
            
            # Core metrics volatility
            day_state.traffic = max(0, int(day_state.traffic * volume_noise))
            day_state.active_users = max(0, int(day_state.active_users * volume_noise))
            day_state.marketing_spend = max(0.0, float(day_state.marketing_spend * random.gauss(1.0, 0.02)))
            day_state.current_ctr = min(1.0, max(0.0, float(day_state.current_ctr * random.gauss(1.0, 0.02))))
            day_state.conversion_rate = min(1.0, max(0.0, float(day_state.conversion_rate * random.gauss(1.0, 0.02))))
            day_state.retention_rate = min(1.0, max(0.0, float(day_state.retention_rate * random.gauss(1.0, 0.005))))
            
            # Mixes volatility
            for m_dict in [day_state.sales_channel_mix, day_state.campaign_mix, day_state.acquisition_mix]:
                for k in m_dict:
                    m_dict[k] = max(0.01, m_dict[k] * random.gauss(1.0, 0.04))
            
            day_state.sales_channel_mix = MixNormalizer.normalize(day_state.sales_channel_mix)
            day_state.campaign_mix = MixNormalizer.normalize(day_state.campaign_mix)
            day_state.acquisition_mix = MixNormalizer.normalize(day_state.acquisition_mix)
            
            # Re-derive downstream metrics to organically inherit the noise
            day_state = DerivedMetricsEngine.compute(day_state)
            
        return persistent_state, day_state
