"""
Generates validation report.
"""
import json
import os
from typing import Dict, Any

class ReportGenerator:
    """Generates a summary validation report for the simulator run."""
    
    def __init__(self, output_path: str):
        self.output_path = output_path
        self.metrics = {
            "rows_generated": 0,
            "trajectories": 0,
            "products": 0,
            "nan_count": 0,
            "negative_orders": 0,
            "negative_inventory": 0
        }
        
    def record_product(self):
        self.metrics["products"] += 1
        
    def record_trajectory(self):
        self.metrics["trajectories"] += 1
        
    def record_state(self, state: Any):
        self.metrics["rows_generated"] += 1
        
        import math
        # simplistic nan check
        if math.isnan(state.revenue):
            self.metrics["nan_count"] += 1
            
        if state.orders < 0:
            self.metrics["negative_orders"] += 1
            
        if state.inventory_available < 0:
            self.metrics["negative_inventory"] += 1

    def save(self):
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(self.metrics, f, indent=2)
