"""
Configuration Loader for Simulator Engine.
Loads the physics data from the JSON config files.
"""
import json
import os
from typing import Dict, Any

class ConfigLoader:
    """
    Loads JSON configuration files for the simulator engine.
    """
    def __init__(self, config_dir: str):
        """
        Initialize the ConfigLoader.
        
        Args:
            config_dir (str): Path to the config directory.
        """
        self.config_dir = config_dir
        self.elasticities = self._load_json("elasticities.json")
        self.archetypes = self._load_json("archetypes.json")
        self.market_graph = self._load_json("market_graph.json")
        self.curve_profiles = self._load_json("curve_profiles.json")
        self.interaction_rules = self._load_json("interaction_rules.json", default=[])
        self.simulation_assumptions = self._load_json("simulation_assumptions.json")

    def _load_json(self, filename: str, default: Any = None) -> Any:
        """
        Load a JSON file from the config directory.
        
        Args:
            filename (str): The filename to load.
            default (Any): Default value if file is not found.
            
        Returns:
            Any: The loaded JSON data.
        """
        path = os.path.join(self.config_dir, filename)
        if not os.path.exists(path):
            if default is not None:
                return default
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_elasticities(self) -> Dict[str, Any]:
        """Get the base elasticities."""
        return self.elasticities

    def get_archetypes(self) -> Dict[str, Any]:
        """Get the archetype overrides."""
        return self.archetypes

    def get_market_graph(self) -> Dict[str, Any]:
        """Get the market state dependency graph."""
        return self.market_graph

    def get_curve_profiles(self) -> Dict[str, Any]:
        """Get the lag-peak-decay curve profiles."""
        return self.curve_profiles

    def get_interaction_rules(self) -> Any:
        """Get the interaction rules."""
        return self.interaction_rules

    def get_simulation_assumptions(self) -> Dict[str, Any]:
        """Get the simulation assumptions."""
        return self.simulation_assumptions
