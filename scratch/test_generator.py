import os
import sys
import json
import traceback

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.history.storage.database import SessionLocal
from src.core.decision.context.engine import ContextEngine
from src.core.decision.hypothesis.generator import HypothesisGenerator
from src.core.history.manager import HistoryManager
from src.api.dependencies import get_forecaster, get_explainer

def test_generator():
    print("======================================================================")
    print("                 DECISION ENGINE GENERATOR DIAGNOSTIC                 ")
    print("======================================================================\n")

    # 1. Initialize dependencies
    db = SessionLocal()
    try:
        print("1. Loading system dependencies...")
        forecaster = get_forecaster()
        explainer = get_explainer()
        history_manager = HistoryManager(db)
        print("Dependencies loaded successfully.\n")
    except Exception as e:
        print(f"CRITICAL: Failed to load forecaster or explainer or database: {e}")
        traceback.print_exc()
        db.close()
        return

    # Initialize HypothesisGenerator
    try:
        generator = HypothesisGenerator(
            db=db,
            forecaster=forecaster,
            explainer=explainer,
            history_manager=history_manager
        )
        print("HypothesisGenerator initialized successfully.")
        print(f"NVIDIA API Key configured: {'Yes (Key matches: ' + generator.api_key[:8] + '...)' if generator.api_key else 'No (Will use fallback templates)'}")
        print("-" * 80)
    except Exception as e:
        print(f"CRITICAL: Failed to initialize HypothesisGenerator: {e}")
        traceback.print_exc()
        db.close()
        return

    # Choose test parameters
    product_id = "P001"
    query = "What will happen if i increase discount by 10%? and increase shipping fee by 20%"
    print(f"Test Query: '{query}'")
    print(f"Test Product ID: '{product_id}'")
    print("-" * 80)

    # 2. Test Step 1: Assemble Business Context (Data Extraction Baseline)
    context = None
    try:
        print("\n=== STEP 2: ASSEMBLING BUSINESS CONTEXT ===")
        context_engine = ContextEngine(db, history_manager=history_manager)
        context = context_engine.assemble_context(query, product_id)
        
        print("\n[Extracted KPI Snapshot]:")
        for k, v in context.get("kpis", {}).items():
            if k not in ["channel_mix", "campaign_mix"]:
                print(f"  {k:25} : {v}")
                
        print("\n[Extracted Rolling Trends]:")
        for k, v in context.get("trends", {}).items():
            print(f"  {k:25} : {v}")
            
        print("\n[Extracted Recent Anomalies]:")
        anomalies = context.get("anomalies", [])
        if not anomalies:
            print("  No anomalies detected.")
        else:
            for idx, anom in enumerate(anomalies[:3], 1):
                print(f"  #{idx} KPI={anom.get('kpi')}, Date={anom.get('date')}, Severity={anom.get('severity')}, Desc={anom.get('description')}")
        print("-" * 80)
    except Exception as e:
        print(f"ERROR during Context Assembly: {e}")
        traceback.print_exc()
        db.close()
        return

    # 3. Test Step 2: Data Extraction in HypothesisGenerator
    print("\n=== STEP 3: DATA EXTRACTION IN HYPOTHESIS GENERATOR ===")
    try:
        # Determine target KPI
        target_kpi = generator._determine_target_kpi(query)
        print(f"\nParsed Target KPI from query: '{target_kpi}'")
        
        # Get SHAP features
        print("\nExtracting SHAP global feature importances...")
        shap_importance = generator._get_shap_features(target_kpi)
        if not shap_importance:
            print("  No SHAP features retrieved (explainer returned empty list).")
        else:
            print(f"  Retrieved {len(shap_importance)} SHAP features. Top 5:")
            for item in shap_importance[:5]:
                print(f"    - {item['feature']:30} ({item['clean_name']}): importance={item['importance_value']:.4f}")
        
        # Get past similar experiments
        print("\nExtracting similar past experiments from database...")
        past_exps = generator._get_past_experiments(target_kpi)
        if not past_exps:
            print("  No past experiments retrieved from DB.")
        else:
            print(f"  Retrieved {len(past_exps)} experiments. Top 3:")
            for exp in past_exps[:3]:
                print(f"    - {exp}")
                
        # Get Knowledge Base rules
        print("\nExtracting business rules from Knowledge Base...")
        kb_rules = generator._get_knowledge_base_rules()
        if not kb_rules:
            print("  No Knowledge Base rules retrieved from DB.")
        else:
            print(f"  Retrieved {len(kb_rules)} rules. Top 3:")
            for rule in kb_rules[:3]:
                print(f"    - {rule}")
        print("-" * 80)
    except Exception as e:
        print(f"ERROR during Data Extraction: {e}")
        traceback.print_exc()

    # 4. Test Step 3: Run Refactored Prioritisation Pipeline
    print("\n=== STEP 4: RUNNING REFACTERED VALIDATION PRIORITY PIPELINE ===")
    try:
        candidates = generator.generate_candidates(context)
        print(f"Pipeline returned {len(candidates)} prioritized hypotheses.")
        
        print("\nCandidate Scored & Ranked Results:")
        print(f"  {'Rank':4} | {'ID':12} | {'Driver':20} | {'Coverage':8} | {'Reliab':6} | {'Intent':6} | {'Diver':5} | {'Priority Score':14} | {'Title'}")
        print(f"  {'-'*4}-+-{'-'*12}-+-{'-'*20}-+-{'-'*8}-+-{'-'*6}-+-{'-'*6}-+-{'-'*5}-+-{'-'*14}-+-{'-'*40}")
        
        for idx, cand in enumerate(candidates, 1):
            print(
                f"  {idx:<4} | {cand.get('hypothesis_id'):12} | "
                f"{cand.get('driver_variable'):20} | "
                f"{cand.get('evidence_coverage', 0.0):<8.2f} | "
                f"{cand.get('historical_reliability', 0.0):<6.2f} | "
                f"{cand.get('intent_match', 0.0):<6.2f} | "
                f"{cand.get('diversity_bonus', 0.0):<5.2f} | "
                f"{cand.get('validation_priority', 0.0):<14.4f} | "
                f"{cand.get('title')}"
            )
            
        print("\nTop Candidates Selected & Schema Details:")
        for idx, cand in enumerate(candidates, 1):
            print(f"\n  {idx}. [{cand.get('hypothesis_id')}] - {cand.get('title')}")
            print(f"     Description : {cand.get('description')}")
            print(f"     Sources     : {cand.get('evidence_sources')}")
            print(f"     Prior Conf  : {cand.get('confidence_prior')}")
            print(f"     Is Primary? : {cand.get('is_primary')}")
            print(f"     Metadata    : {json.dumps(cand.get('generator_metadata'), indent=4)}")
            
        print("-" * 80)
    except Exception as e:
        print(f"ERROR during candidate generation: {e}")
        traceback.print_exc()

    db.close()
    print("\nDiagnostic complete!")

if __name__ == "__main__":
    test_generator()
