import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.history.storage.database import SessionLocal
from src.core.history.storage.models import Pattern

def verify():
    db = SessionLocal()
    try:
        count = db.query(Pattern).filter(Pattern.pattern_type == "trend").count()
        print(f"Total seeded trend records: {count}")
        
        # Display the first 5 records
        records = db.query(Pattern).filter(Pattern.pattern_type == "trend").limit(5).all()
        print("\nFirst 5 Records:")
        for r in records:
            print(f"ID: {r.id} | Product: {r.product_id} | KPI: {r.kpi} | Date: {r.date} | Value: {r.value:.4f}")
            
    except Exception as e:
        print(f"Query failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify()
