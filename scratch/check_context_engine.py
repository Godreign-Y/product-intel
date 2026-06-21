import os
import sys
import json
import datetime
import traceback

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.history.storage.database import SessionLocal
from src.core.decision.context.engine import ContextEngine

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def check_engine():
    db = SessionLocal()
    try:
        print("Initializing ContextEngine...")
        engine = ContextEngine(db)
        
        product_id = "P001"
        query = "What happens if we increase discounts by 15%?"
        print(f"\nAssembling context for Product: {product_id} and Query: '{query}'...")
        
        context = engine.assemble_context(query=query, product_id=product_id)
        
        print("\n================== ASSEMBLED CONTEXT RESULTS ==================")
        print(f"Product ID: {context['product_id']}")
        print(f"Assembled At: {context['assembled_at']}")
        
        # 1. KPIs
        print("\n--- 1. Baseline KPIs Snapshot ---")
        kpis = context.get("kpis", {})
        for k, v in kpis.items():
            if k not in ["channel_mix", "campaign_mix"]:
                print(f"  {k:25} : {v}")
        
        print("\n  Sales Channel Mix:")
        for k, v in kpis.get("channel_mix", {}).items():
            print(f"    - {k:15} : {v}%")
            
        print("\n  Marketing Campaign Mix:")
        for k, v in kpis.get("campaign_mix", {}).items():
            print(f"    - {k:15} : {v}%")
            
        # 2. Trends
        print("\n--- 2. Rolling Trends ---")
        trends = context.get("trends", {})
        for k, v in trends.items():
            print(f"  {k:25} : {v}")
            
        # 3. Anomalies
        print("\n--- 3. Recent Anomalies (Last 30 Days) ---")
        anomalies = context.get("anomalies", [])
        if not anomalies:
            print("  No anomalies detected.")
        else:
            for idx, anom in enumerate(anomalies, 1):
                print(f"  Anomaly #{idx}:")
                print(f"    Date       : {anom.get('date')}")
                print(f"    KPI        : {anom.get('kpi')}")
                print(f"    Value      : {anom.get('value')}")
                print(f"    Severity   : {anom.get('severity')}")
                print(f"    Description: {anom.get('description')}")
                print()
                
        print("===============================================================")
        
    except Exception as e:
        print("Failed to execute context engine check:")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_engine()
