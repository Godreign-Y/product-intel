"""
Core models for the Simulator Engine.
"""
from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class BusinessState:
    """
    Represents the business state on a specific day.
    """
    inventory_available: int = 0
    
    avg_selling_price: float = 0.0
    effective_price: float = 0.0
    discount_pct: float = 0.0
    shipping_fee: float = 0.0
    
    marketing_spend: float = 0.0
    
    sales_channel_mix: Dict[str, float] = field(default_factory=dict)
    campaign_mix: Dict[str, float] = field(default_factory=dict)
    acquisition_mix: Dict[str, float] = field(default_factory=dict)
    
    traffic: int = 0
    active_users: int = 0
    current_ctr: float = 0.0
    current_roas: float = 0.0
    
    orders: int = 0
    fulfilled_orders: int = 0
    revenue: float = 0.0
    profit: float = 0.0
    
    conversion_rate: float = 0.0
    retention_rate: float = 0.0
    avg_ltv: float = 0.0

@dataclass
class SimulationConfig:
    """
    Configuration parameters for a simulation run.
    """
    simulation_days: int = 365
    random_seed: int = 42
    noise_enabled: bool = True
    seasonality_enabled: bool = True
    interaction_enabled: bool = True
    buffer_size: int = 100000
