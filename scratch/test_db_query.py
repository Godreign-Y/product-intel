import os
import sys
import traceback

# Add the project root to sys.path
sys.path.append(r"c:\Users\Relanto\OneDrive - Relanto\new\sprint2_product_intel")

from src.core.history.storage.database import SessionLocal
from src.core.history.manager import HistoryManager

def test():
    db = SessionLocal()
    print("Database dialect:", db.bind.dialect.name)
    try:
        manager = HistoryManager(db)
        print("Testing get_trend_direction dynamically...")
        dir_rev = manager.get_trend_direction("P001", "revenue")
        dir_ord = manager.get_trend_direction("P001", "orders")
        print(f"P001 Revenue Trend: {dir_rev}")
        print(f"P001 Orders Trend: {dir_ord}")
    except Exception as e:
        print("Failed with exception:")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test()
