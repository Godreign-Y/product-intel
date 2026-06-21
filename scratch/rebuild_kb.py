import os
import sys
import json
import traceback

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.history.storage.database import SessionLocal
from src.core.history.manager import HistoryManager
from src.core.history.storage.models import KnowledgeBase

def rebuild_kb_main():
    print("======================================================================")
    print("                 KNOWLEDGE BASE REBUILD PIPELINE                      ")
    print("======================================================================\n")

    db = SessionLocal()
    try:
        print("Instantiating HistoryManager...")
        manager = HistoryManager(db)
        
        print("\nTriggering rebuild_knowledge_base(). This aggregates 1,600+ experiments...")
        summary = manager.rebuild_knowledge_base()
        
        print("\nRebuild Successful! Direct aggregation summary:")
        print(f"  {'Topic/Driver Name':30} | {'Aggregated Experiments Count':30}")
        print(f"  {'-'*30}-+-{'-'*30}")
        for topic, count in sorted(summary.items(), key=lambda x: x[1], reverse=True):
            print(f"  {topic:30} | {count:30}")
            
        print(f"\nTotal unique rules populated: {len(summary)}")
        
        # Pull a sample rule to verify
        print("\nRetrieving sample rule from DB KnowledgeBase table:")
        sample = db.query(KnowledgeBase).filter(KnowledgeBase.pattern_type == "discount_pct").first()
        if sample:
            print(f"  Topic/Driver: {sample.pattern_type}")
            print(f"  Confidence  : {sample.confidence_score}")
            print(f"  Rules JSON  :")
            print(json.dumps(sample.synthesized_rules, indent=4))
        else:
            print("  No sample rules found for discount_pct.")
            
    except Exception as e:
        print(f"ERROR: Knowledge Base rebuild pipeline failed: {e}")
        traceback.print_exc()
    finally:
        db.close()
        print("\nPipeline execution complete!")

if __name__ == "__main__":
    rebuild_kb_main()
