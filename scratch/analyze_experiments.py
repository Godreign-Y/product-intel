import os
import sys
import pandas as pd
from sqlalchemy import func

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.history.storage.database import SessionLocal
from src.core.history.storage.models import Experiment

def analyze_experiments():
    db = SessionLocal()
    try:
        print("=== EXPERIMENTS TABLE ANALYSIS ===")
        total_count = db.query(Experiment).count()
        print(f"Total experiments count: {total_count}")
        
        # 1. Driver distribution
        print("\n1. Driver column distribution:")
        drivers = db.query(Experiment.driver, func.count(Experiment.id)).group_by(Experiment.driver).all()
        for d, count in drivers:
            print(f"   - {d}: {count}")
            
        # 2. Outcome/Result distribution
        print("\n2. Outcome column distribution:")
        outcomes = db.query(Experiment.outcome, func.count(Experiment.id)).group_by(Experiment.outcome).all()
        for o, count in outcomes:
            print(f"   - {o}: {count}")
            
        print("\n3. Result column distribution:")
        results = db.query(Experiment.result, func.count(Experiment.id)).group_by(Experiment.result).all()
        for r, count in results:
            print(f"   - {r}: {count}")
            
        # 4. Category distribution (top 10)
        print("\n4. Top 10 Product Categories:")
        categories = db.query(Experiment.category, func.count(Experiment.id)).group_by(Experiment.category).order_by(func.count(Experiment.id).desc()).limit(10).all()
        for cat, count in categories:
            print(f"   - {cat}: {count}")
            
        # 5. Type distribution
        print("\n5. Experiment Type distribution:")
        types = db.query(Experiment.type, func.count(Experiment.id)).group_by(Experiment.type).order_by(func.count(Experiment.id).desc()).limit(10).all()
        for t, count in types:
            print(f"   - {t}: {count}")
            
        # 6. Sample records
        print("\n6. Sample records from experiments table:")
        samples = db.query(Experiment).limit(5).all()
        for idx, s in enumerate(samples, 1):
            print(f"\n   --- Sample #{idx} ---")
            print(f"   Experiment ID  : {s.experiment_id}")
            print(f"   Driver         : {s.driver}")
            print(f"   Outcome/Result : {s.outcome} / {s.result}")
            print(f"   Primary Metric : {s.primary_metric}")
            print(f"   Change Summary : {s.change_summary}")
            print(f"   Notes          : {s.notes}")
            
    except Exception as e:
        print(f"Error during analysis: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    analyze_experiments()
