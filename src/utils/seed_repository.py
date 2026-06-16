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
    csv_path = "temporal_dataset.csv"
    if not os.path.exists(csv_path):
        logger.error(f"Historical dataset CSV not found at {csv_path}. Seeding aborted.")
        return
        
    logger.info(f"Reading historical dataset from {csv_path}...")
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} records.")
    
    # Initialize DB Session
    db = SessionLocal()
    try:
        manager = HistoryManager(db)
        
        logger.info("Starting historical intelligence repository build pipeline...")
        result = manager.run_build_pipeline(df, force_rebuild=True)
        
        logger.info("Seeding pipeline completed successfully!")
        logger.info(f" - Snapshots created: {result['snapshots_created']}")
        logger.info(f" - Events detected: {result['events_detected']}")
        logger.info(f" - Experiments inferred: {result['experiments_inferred']}")
        logger.info(f" - Reports generated: {result['reports_generated']}")
        
    except Exception as e:
        logger.error(f"Seeding pipeline failed: {e}", exc_info=True)
    finally:
        db.close()

if __name__ == "__main__":
    main()
