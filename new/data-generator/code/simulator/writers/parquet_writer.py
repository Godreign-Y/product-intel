"""
Parquet stream writer to persist trajectories efficiently.
"""
import pyarrow as pa
import pyarrow.parquet as pq
from typing import Dict, Any, List
from simulator.core.models import BusinessState
import os

class ParquetStreamWriter:
    """Writes simulation data incrementally to parquet files."""
    
    def __init__(self, output_dir: str, buffer_size: int = 100000):
        self.output_dir = output_dir
        self.buffer_size = buffer_size
        self.buffer: List[Dict[str, Any]] = []
        self.part_counter = 0
        os.makedirs(output_dir, exist_ok=True)
        
    def _state_to_dict(self, traj_id: str, sched_id: str, prod_id: str, day: int, state: BusinessState) -> Dict[str, Any]:
        d = {
            "trajectory_id": traj_id,
            "schedule_id": sched_id,
            "product_id": prod_id,
            "day": day,
            "inventory_available": state.inventory_available,
            "avg_selling_price": state.avg_selling_price,
            "discount_pct": state.discount_pct,
            "shipping_fee": state.shipping_fee,
            "marketing_spend": state.marketing_spend,
            "traffic": state.traffic,
            "active_users": state.active_users,
            "current_ctr": state.current_ctr,
            "current_roas": state.current_roas,
            "orders": state.orders,
            "revenue": state.revenue,
            "profit": state.profit,
            "conversion_rate": state.conversion_rate,
            "retention_rate": state.retention_rate,
            "avg_ltv": state.avg_ltv
        }
        return d

    def append(self, traj_id: str, sched_id: str, prod_id: str, day: int, state: BusinessState):
        self.buffer.append(self._state_to_dict(traj_id, sched_id, prod_id, day, state))
        if len(self.buffer) >= self.buffer_size:
            self.flush()

    def flush(self):
        if not self.buffer:
            return
            
        table = pa.Table.from_pylist(self.buffer)
        filepath = os.path.join(self.output_dir, f"part_{self.part_counter:03d}.parquet")
        pq.write_table(table, filepath)
        
        self.part_counter += 1
        self.buffer.clear()
