import os
import sys
import pandas as pd
import numpy as np
import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.history.storage.database import SessionLocal, engine
from src.core.history.storage.models import Pattern, Base

def seed_trends():
    db = SessionLocal()
    try:
        # Ensure table is created
        Base.metadata.create_all(bind=engine)
        
        # Clear existing trend patterns
        print("Clearing existing trend patterns...")
        db.query(Pattern).filter(Pattern.pattern_type == "trend").delete()
        db.commit()
        
        csv_path = "temporal_dataset.csv"
        if not os.path.exists(csv_path):
            print(f"Dataset {csv_path} not found.")
            return
            
        print(f"Loading dataset {csv_path}...")
        df = pd.read_csv(csv_path)
        df["date"] = pd.to_datetime(df["date"])
        
        unique_products = df["product_id"].unique()
        print(f"Calculating trends for {len(unique_products)} products...")
        
        patterns_to_add = []
        for product_id in unique_products:
            prod_df = df[df["product_id"] == product_id].sort_values("date")
            if len(prod_df) < 10:
                continue
                
            latest_date = prod_df["date"].max().date()
            
            # Use a 30-day window to calculate trend
            recent_df = prod_df.tail(30)
            half = len(recent_df) // 2
            first_half = recent_df.iloc[:half]
            second_half = recent_df.iloc[half:]
            
            for kpi in ["revenue", "orders"]:
                m1 = first_half[kpi].mean()
                m2 = second_half[kpi].mean()
                
                if m1 > 0:
                    val = (m2 - m1) / m1
                else:
                    val = 0.0
                    
                # Clip value between -1.0 and 1.0 to avoid outliers
                val = float(np.clip(val, -1.0, 1.0))
                
                pattern = Pattern(
                    pattern_type="trend",
                    product_id=str(product_id),
                    kpi=kpi,
                    date=latest_date,
                    value=val,
                    details={"method": "rolling_window_pct_change", "window_days": len(recent_df)}
                )
                patterns_to_add.append(pattern)
                
        print(f"Saving {len(patterns_to_add)} trend pattern records to the database...")
        db.add_all(patterns_to_add)
        db.commit()
        print("Trends seeded successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Seeding failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_trends()
