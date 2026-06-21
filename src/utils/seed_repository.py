import os
import sys
import pandas as pd

# Adjust path to find src package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.core.history.storage.database import SessionLocal, engine, Base
from src.core.history.manager import HistoryManager
from src.utils.logger import setup_logger

logger = setup_logger("seed_repository")

def main():
    csv_path = "experiment_dataset.csv"
    if not os.path.exists(csv_path):
        logger.error(f"Experiment dataset CSV not found at {csv_path}. Seeding aborted.")
        return
        
    # Initialize DB Session
    db = SessionLocal()
    try:
        manager = HistoryManager(db)
        
        logger.info("Starting historical intelligence repository build pipeline...")
        result = manager.run_build_pipeline(force_rebuild=True, csv_path=csv_path)
        
        logger.info("Seeding pipeline completed successfully!")
        logger.info(f" - Experiments recorded and indexed: {result['experiments_recorded']}")
        
    except Exception as e:
        logger.error(f"Seeding pipeline failed: {e}", exc_info=True)
    finally:
        db.close()

if __name__ == "__main__":
    main()
