import os
import sys
import traceback
from sqlalchemy.orm import Session

# Add the project root to sys.path
sys.path.append(r"c:\Users\Relanto\OneDrive - Relanto\new\sprint2_product_intel")

from src.core.history.storage.database import SessionLocal, engine
from src.core.history.manager import HistoryManager

def test():
    db = SessionLocal()
    print("Database dialect:", db.bind.dialect.name)
    try:
        manager = HistoryManager(db)
        print("Running semantic_search...")
        results = manager.semantic_search("discounts", limit=5)
        print("Success! Found results:", len(results))
    except Exception as e:
        print("Failed with exception:")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test()
