"""
Interaction physics to apply synergies and saturation.
"""
from typing import Dict, Any, List

class InteractionEngine:
    """
    Applies interaction rules like synergy, cannibalization, saturation, and suppression
    between concurrent active actions.
    """
    def __init__(self, rules: List[Dict[str, Any]]):
        """
        Initialize the InteractionEngine.
        
        Args:
            rules (List[Dict[str, Any]]): List of interaction rule definitions.
        """
        self.rules = rules

    def apply_interactions(self, base_effects: Dict[str, float], active_actions: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Apply interaction multipliers based on active actions.
        
        Args:
            base_effects (Dict[str, float]): The baseline effects calculated.
            active_actions (List[Dict[str, Any]]): Currently active actions.
            
        Returns:
            Dict[str, float]: Final interaction-adjusted effects.
        """
        adjusted_effects = dict(base_effects)
        active_features = {act.get("feature") for act in active_actions}
        
        for rule in self.rules:
            action_a = rule.get("action_a")
            action_b = rule.get("action_b")
            multiplier = rule.get("multiplier", 1.0)
            
            # If both actions are active
            if action_a in active_features and action_b in active_features:
                if action_a in adjusted_effects:
                    adjusted_effects[action_a] *= multiplier
                if action_b in adjusted_effects:
                    adjusted_effects[action_b] *= multiplier
                    
        return adjusted_effects
