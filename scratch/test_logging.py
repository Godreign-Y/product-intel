import os
import sys
import logging

# Ensure project root is in sys.path
sys.path.append(r"c:\Users\Relanto\OneDrive - Relanto\new\sprint2_product_intel")

# Configure root logger to output debug info to stdout
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] [%(name)s:%(lineno)d] %(message)s",
    stream=sys.stdout
)

from src.core.history.storage.database import SessionLocal
from src.api.routers.decision import get_decision_manager

def main():
    print("Initializing Database Session...")
    db = SessionLocal()
    try:
        print("Building DecisionManager from AppState...")
        manager = get_decision_manager(db)
        
        print("\nExecuting process_decision_flow...")
        result = manager.process_decision_flow(
            query="What might happen if we increase discounts by 10%?",
            product_id="P001",
            session_id="test_logging_session_123"
        )
        print("\nFlow completed successfully. Brief summary:")
        print("Context ID:", result.get("context_id"))
        print("Ranked hypotheses count:", len(result.get("ranked_hypotheses", [])))
        print("Recommendations count:", len(result.get("recommendations", [])))
    except Exception as e:
        print("\nExecution failed with error:")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
