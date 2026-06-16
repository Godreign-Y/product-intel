"""
CSV stream writer to persist trajectories efficiently.
"""
import csv
from typing import Dict, Any, List
from simulator.core.models import BusinessState
import os

class CsvStreamWriter:
    """Writes simulation data incrementally to a CSV file."""
    
    def __init__(self, output_dir: str, filename: str = "dataset.csv", buffer_size: int = 100000):
        self.output_dir = output_dir
        self.buffer_size = buffer_size
        self.buffer: List[Dict[str, Any]] = []
        os.makedirs(output_dir, exist_ok=True)
        self.filepath = os.path.join(self.output_dir, filename)
        self.fieldnames = [
            "trajectory_id", "schedule_id", "product_id", "day",
            "inventory_available", "avg_selling_price", "effective_price", "discount_pct", "shipping_fee",
            "marketing_spend", "traffic", "active_users", "current_ctr", "current_roas",
            "orders", "fulfilled_orders", "revenue", "profit", "conversion_rate", "retention_rate", "avg_ltv",
            "sales_mix_amazon", "sales_mix_website", "sales_mix_nykaa", "sales_mix_mobile_app",
            "campaign_mix_search", "campaign_mix_social", "campaign_mix_email", "campaign_mix_affiliate",
            "acq_mix_google", "acq_mix_instagram", "acq_mix_facebook", "acq_mix_organic", "acq_mix_referral", "acq_mix_email",
            "category_id", "age_mix_0_25", "age_mix_25_45", "age_mix_45_plus"
        ]
        
        # Write header
        with open(self.filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writeheader()
        
    def _state_to_dict(self, traj_id: str, sched_id: str, prod_id: str, day: int, state: BusinessState) -> Dict[str, Any]:
        d = {
            "trajectory_id": traj_id,
            "schedule_id": sched_id,
            "product_id": prod_id,
            "day": day,
            "inventory_available": state.inventory_available,
            "avg_selling_price": state.avg_selling_price,
            "effective_price": state.effective_price,
            "discount_pct": state.discount_pct,
            "shipping_fee": state.shipping_fee,
            "marketing_spend": state.marketing_spend,
            "traffic": state.traffic,
            "active_users": state.active_users,
            "current_ctr": state.current_ctr,
            "current_roas": state.current_roas,
            "orders": state.orders,
            "fulfilled_orders": state.fulfilled_orders,
            "revenue": state.revenue,
            "profit": state.profit,
            "conversion_rate": state.conversion_rate,
            "retention_rate": state.retention_rate,
            "avg_ltv": state.avg_ltv,
            "sales_mix_amazon": state.sales_channel_mix.get("amazon", 0.0),
            "sales_mix_website": state.sales_channel_mix.get("website", 0.0),
            "sales_mix_nykaa": state.sales_channel_mix.get("nykaa", 0.0),
            "sales_mix_mobile_app": state.sales_channel_mix.get("mobile_app", 0.0),
            "campaign_mix_search": state.campaign_mix.get("search", 0.0),
            "campaign_mix_social": state.campaign_mix.get("social", 0.0),
            "campaign_mix_email": state.campaign_mix.get("email", 0.0),
            "campaign_mix_affiliate": state.campaign_mix.get("affiliate", 0.0),
            "acq_mix_google": state.acquisition_mix.get("google", 0.0),
            "acq_mix_instagram": state.acquisition_mix.get("instagram", 0.0),
            "acq_mix_facebook": state.acquisition_mix.get("facebook", 0.0),
            "acq_mix_organic": state.acquisition_mix.get("organic", 0.0),
            "acq_mix_referral": state.acquisition_mix.get("referral", 0.0),
            "acq_mix_email": state.acquisition_mix.get("email", 0.0),
            "category_id": state.category_id,
            "age_mix_0_25": state.age_group_mix.get("0-25", 0.0),
            "age_mix_25_45": state.age_group_mix.get("25-45", 0.0),
            "age_mix_45_plus": state.age_group_mix.get("45+", 0.0)
        }
        return d

    def append(self, traj_id: str, sched_id: str, prod_id: str, day: int, state: BusinessState):
        self.buffer.append(self._state_to_dict(traj_id, sched_id, prod_id, day, state))
        if len(self.buffer) >= self.buffer_size:
            self.flush()

    def flush(self):
        if not self.buffer:
            return
            
        with open(self.filepath, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writerows(self.buffer)
            
        self.buffer.clear()
