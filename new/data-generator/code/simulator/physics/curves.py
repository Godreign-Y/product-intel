"""
Curves logic for the Simulator Engine.
Implements Piecewise Linear Rise + Exponential Decay.
"""
import math
from typing import Dict, Any

class CurveEngine:
    """
    Computes the effect multiplier for a given action over time based on lag, peak, and decay profiles.
    """
    def __init__(self, curve_profiles: Dict[str, Any]):
        """
        Initialize the CurveEngine.
        
        Args:
            curve_profiles (Dict[str, Any]): Loaded curve profiles mapping.
        """
        self.profiles = curve_profiles

    def compute_multiplier(self, profile_name: str, elapsed_days: int) -> float:
        """
        Calculate the effect strength multiplier over time.
        
        Args:
            profile_name (str): The name of the curve profile to use.
            elapsed_days (int): Days elapsed since the event started.
            
        Returns:
            float: A multiplier between 0.0 and 1.0.
        """
        profile = self.profiles.get(profile_name)
        if not profile:
            # Fallback to immediate profile if not found
            lag = 0
            peak = 1
            decay = 3
        else:
            lag = profile.get("lag_days", 0)
            peak = profile.get("peak_days", 1)
            decay = profile.get("decay_days", 1)

        # Before lag completes, no effect
        if elapsed_days < lag:
            return 0.0
            
        # If no peak/decay is specified (e.g. seasonal), we assume immediate 1.0
        if peak == 0 and decay == 0:
            return 1.0

        days_active = elapsed_days - lag
        
        # Linear Rise to peak
        if days_active <= peak:
            if peak == 0:
                return 1.0
            return days_active / peak
            
        # Exponential Decay after peak
        days_decaying = days_active - peak
        if decay <= 0:
            return 0.0
            
        # Exponential decay: e^(-lambda * t) where lambda = ln(2) / half_life
        # We assume decay_days is roughly 3-4 half-lives. Let's use lambda = 3 / decay_days
        decay_constant = 3.0 / decay
        multiplier = math.exp(-decay_constant * days_decaying)
        return max(0.0, multiplier)
