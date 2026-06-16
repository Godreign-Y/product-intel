import pandas as pd
import json
import os
import sys

from validator.data_quality import DataQualityValidator
from validator.elasticity_validator import ElasticityValidator
from validator.causality_validator import CausalityValidator

def run_validation():
    csv_path = "output/trajectories_v8.csv"
    
    if not os.path.exists(csv_path):
        print(f"Error: Could not find {csv_path}")
        sys.exit(1)
        
    print(f"Loading {csv_path}...")
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} rows.")
    
    final_report = {
        "rows": len(df),
        "nan_count": 0,
        "negative_inventory": 0,
        "negative_orders": 0,
        "negative_revenue": 0,
        "mix_violations": 0,
        "stockout_events": 0,
        "restock_events": 0,
        "validation_passed": True
    }
    
    print("Running Data Quality Checks...")
    dq = DataQualityValidator(df)
    dq_res = dq.validate_all()
    
    print("Running Elasticity Checks...")
    ev = ElasticityValidator(df)
    ev_res = ev.validate_all()
    
    print("Running Causality Checks...")
    cv = CausalityValidator(df)
    cv_res = cv.validate_all()
    
    # Compile final report structure for clarity
    final_report = {
        "summary": {
            "rows_processed": len(df),
            "validation_passed": True,
        },
        "data_quality_checks": {
            "passed": True,
            "nan_count": dq_res.get("nan_count", 0),
            "bounds_violations": dq_res.get("bounds_violations", 0),
            "derived_violations": dq_res.get("derived_violations", 0),
            "mix_violations": dq_res.get("mix_violations", 0),
            "negative_inventory": dq_res.get("negative_inventory", 0),
            "stockout_events": dq_res.get("stockout_events", 0),
            "restock_events": dq_res.get("restock_events", 0)
        },
        "elasticity_checks": {
            "passed": True,
            "events_analyzed": ev_res.get("events_analyzed", 0),
            "status": ev_res.get("elasticity_validation", "Failed"),
            "failed_events": ev_res.get("failed_events", [])
        },
        "causality_checks": {
            "passed": cv_res.get("causality_passed", True),
            "correlations": cv_res.get("causality_correlations", {}),
            "failed_correlations": cv_res.get("failed_correlations", [])
        }
    }
    
    # Assess failures
    if final_report["data_quality_checks"]["bounds_violations"] > 0 or \
       final_report["data_quality_checks"]["derived_violations"] > 0 or \
       final_report["data_quality_checks"]["mix_violations"] > 0:
        final_report["data_quality_checks"]["passed"] = False
        final_report["summary"]["validation_passed"] = False
        
    if final_report["elasticity_checks"]["status"] != "Passed":
        final_report["elasticity_checks"]["passed"] = False
        final_report["summary"]["validation_passed"] = False
        
    if not final_report["causality_checks"]["passed"]:
        final_report["summary"]["validation_passed"] = False

    # Ensure output path exists
    report_path = "../docs/25_simulation_report.json"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, "w") as f:
        json.dump(final_report, f, indent=2)
        
    print(f"Validation complete. Report written to {report_path}")
    print("\n--- VALIDATION SUMMARY ---")
    print(f"Data Quality: {'PASS' if final_report['data_quality_checks']['passed'] else 'FAIL'}")
    print(f"Elasticity:   {'PASS' if final_report['elasticity_checks']['passed'] else 'FAIL'}")
    print(f"Causality:    {'PASS' if final_report['causality_checks']['passed'] else 'FAIL'}")
    print(f"OVERALL:      {'PASS' if final_report['summary']['validation_passed'] else 'FAIL'}")
    
    if not final_report['summary']['validation_passed']:
        print("\n--- FAILURE DETAILS ---")
        if not final_report['causality_checks']['passed']:
            print("\nFailed Correlations:")
            for fc in final_report['causality_checks']['failed_correlations']:
                print(f"  - {fc}")
        
        if not final_report['elasticity_checks']['passed']:
            print(f"\nFailed Elasticity Events (Sample of {len(final_report['elasticity_checks']['failed_events'])}):")
            for fe in final_report['elasticity_checks']['failed_events'][:10]:
                print(f"  - {fe['type']} at Day {fe['day']} for {fe['trajectory']}: {fe}")

if __name__ == "__main__":
    run_validation()
