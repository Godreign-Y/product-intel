import os
import sys
import traceback
import pandas as pd
import numpy as np

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.dependencies import get_forecaster, get_explainer, get_historical_df_from_db

def test_shap_values():
    print("======================================================================")
    print("                      SHAP VALUES DIAGNOSTIC SYSTEM                  ")
    print("======================================================================\n")

    # 1. Initialize Forecaster and Explainer
    try:
        print("Initializing Forecaster and SHAP Explainer...")
        forecaster = get_forecaster()
        explainer = get_explainer()
        print("Initialization successful!")
        print(f"Loaded target models: {list(forecaster.models.keys())}")
        print(f"Initialized explainers: {list(explainer.explainers.keys())}")
        print(f"Background samples loaded: {list(explainer.background_samples.keys())}")
        print("-" * 70)
    except Exception as e:
        print("CRITICAL: Failed to initialize forecaster or explainer!")
        traceback.print_exc()
        return

    # 2. Test Global Feature Importance
    print("\n--- 2. Testing Global Feature Importance for all KPI targets ---")
    kpis = ["revenue", "profit", "orders", "conversion_rate", "retention_rate"]
    
    for kpi in kpis:
        print(f"\nTarget KPI: {kpi.upper()}")
        try:
            # Check if background sample exists to know if using expectation-based SHAP or fallback
            has_bg = kpi in explainer.background_samples or kpi.title() in explainer.background_samples
            explainer_type = "Expectation-based SHAP (using background sample)" if has_bg else "Gain-based Model Feature Importance (fallback)"
            print(f"Explainer Type: {explainer_type}")
            
            global_importance = explainer.get_global_importance(kpi)
            print(f"Successfully retrieved global importance (top {len(global_importance)} features):")
            
            print(f"  {'Feature Code':30} | {'Business Clean Name':35} | {'Importance Value':16}")
            print(f"  {'-'*30}-+-{'-'*35}-+-{'-'*16}")
            for item in global_importance[:10]:
                print(f"  {item['feature']:30} | {item['clean_name']:35} | {item['importance_value']:16.4f}")
        except Exception as e:
            print(f"ERROR computing global importance for {kpi}: {str(e)}")
            traceback.print_exc()
        print("-" * 70)

    # 3. Load historical data and select test case
    print("\n--- 3. Fetching Sample Product for Local Explanation Testing ---")
    try:
        df_hist = get_historical_df_from_db()
        if df_hist.empty:
            print("ERROR: Historical dataset is empty!")
            return
            
        print(f"Loaded dataset with {len(df_hist)} rows.")
        unique_prods = df_hist["product_id"].unique()
        print(f"Unique products count: {len(unique_prods)}")
        
        # Pick first product with enough rows
        product_id = None
        for pid in unique_prods:
            subset = df_hist[df_hist["product_id"] == pid]
            if len(subset) >= 10:
                product_id = pid
                break
                
        if not product_id:
            product_id = unique_prods[0]
            
        print(f"Selected Product for testing: {product_id}")
        prod_data = df_hist[df_hist["product_id"] == product_id].sort_values(by="date")
        print(f"Data rows for product: {len(prod_data)}")
        print(f"Date range: {prod_data['date'].min()} to {prod_data['date'].max()}")
        
        # 4. Test Historical Date Local Explanation
        hist_date = prod_data["date"].iloc[-1].strftime("%Y-%m-%d")
        print(f"\n--- 4. Testing Historical Explanation for Date: {hist_date} ---")
        
        for kpi in ["revenue", "profit", "orders"]:
            print(f"\nExplaining prediction for KPI: {kpi.upper()} on {hist_date}")
            try:
                explanation = explainer.explain_prediction(
                    historical_df=df_hist,
                    product_id=product_id,
                    target_metric=kpi,
                    date=hist_date
                )
                
                print("Prediction Value :", explanation["prediction_value"])
                print("Baseline Value   :", explanation["base_value"])
                print("Summary          :", explanation["explanation_summary"])
                
                print("\n  Top Positive Drivers:")
                for item in explanation["positive_drivers"][:3]:
                    print(f"    - {item['clean_name']} ({item['feature']}): value={item['actual_value']:.4f}, SHAP={item['shap_value']:.4f}")
                    
                print("\n  Top Negative Drivers:")
                for item in explanation["negative_drivers"][:3]:
                    print(f"    - {item['clean_name']} ({item['feature']}): value={item['actual_value']:.4f}, SHAP={item['shap_value']:.4f}")
            except Exception as e:
                print(f"ERROR explaining prediction for {kpi}: {str(e)}")
                traceback.print_exc()
            print("-" * 70)

        # 5. Test Future Date Local Explanation (requires forecasting first)
        max_date = prod_data["date"].max()
        future_date = (max_date + pd.Timedelta(days=5)).strftime("%Y-%m-%d")
        print(f"\n--- 5. Testing Future Explanation (requires forecast) for Date: {future_date} ---")
        
        for kpi in ["revenue", "profit", "orders"]:
            print(f"\nExplaining prediction for KPI: {kpi.upper()} on {future_date} (future date)")
            try:
                explanation = explainer.explain_prediction(
                    historical_df=df_hist,
                    product_id=product_id,
                    target_metric=kpi,
                    date=future_date
                )
                
                print("Prediction Value :", explanation["prediction_value"])
                print("Baseline Value   :", explanation["base_value"])
                print("Summary          :", explanation["explanation_summary"])
                
                print("\n  Top Positive Drivers:")
                for item in explanation["positive_drivers"][:3]:
                    print(f"    - {item['clean_name']} ({item['feature']}): value={item['actual_value']:.4f}, SHAP={item['shap_value']:.4f}")
                    
                print("\n  Top Negative Drivers:")
                for item in explanation["negative_drivers"][:3]:
                    print(f"    - {item['clean_name']} ({item['feature']}): value={item['actual_value']:.4f}, SHAP={item['shap_value']:.4f}")
            except Exception as e:
                print(f"ERROR explaining prediction for {kpi}: {str(e)}")
                traceback.print_exc()
            print("-" * 70)

    except Exception as e:
        print(f"General error during local explanation tests: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    test_shap_values()
