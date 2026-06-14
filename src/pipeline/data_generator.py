import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_synthetic_data(output_path: str, num_products: int = 30, days: int = 1100):
    np.random.seed(42)
    
    # Define categories and base attributes for products
    categories = ["Electronics", "Apparel", "Home_Kitchen", "Beauty", "Fitness"]
    products_metadata = []
    for i in range(1, num_products + 1):
        prod_id = f"PROD_{i:03d}"
        category = np.random.choice(categories)
        base_price = np.random.uniform(15.0, 150.0)
        cogs_pct = np.random.uniform(0.35, 0.55) # Cost of Goods Sold percentage
        base_retention = np.random.uniform(0.10, 0.35)
        products_metadata.append({
            "Product_ID": prod_id,
            "Category": category,
            "Base_Price": base_price,
            "COGS_Pct": cogs_pct,
            "Base_Retention": base_retention
        })
    
    df_meta = pd.DataFrame(products_metadata)
    
    # Generate dates
    start_date = datetime(2023, 1, 1)
    date_list = [start_date + timedelta(days=x) for x in range(days)]
    
    rows = []
    for date in date_list:
        is_weekend = date.weekday() >= 5
        # Seasonality factors
        month_factor = 1.0 + 0.15 * np.sin(2 * np.pi * date.month / 12)  # Peak in summer / winter
        holiday_factor = 1.3 if (date.month == 11 and date.day >= 20) or (date.month == 12 and date.day <= 25) else 1.0
        
        for idx, row in df_meta.iterrows():
            prod_id = row["Product_ID"]
            category = row["Category"]
            base_price = row["Base_Price"]
            cogs_pct = row["COGS_Pct"]
            base_retention = row["Base_Retention"]
            
            # Pricing & Promotion decisions
            # 15% chance of promotion, else low or no discount
            if np.random.rand() < 0.15:
                discount_pct = np.random.choice([0.1, 0.15, 0.20, 0.30])
            else:
                discount_pct = np.random.uniform(0.0, 0.05)
                
            price = base_price * (1 - discount_pct)
            
            # Shipping fee choices (standard, low, free)
            shipping_fee = np.random.choice([0.0, 4.99, 9.99], p=[0.2, 0.6, 0.2])
            
            # Marketing decisions: base marketing + weekend spikes + campaign promotions
            base_marketing = np.random.uniform(5, 50)
            if discount_pct > 0.1:
                marketing_spend = base_marketing * np.random.uniform(2.0, 5.0)
            else:
                marketing_spend = base_marketing
                
            # Traffic (Views): driven by marketing, product category, weekend, month factor, holiday factor
            category_traffic_weight = {"Electronics": 1.5, "Apparel": 1.2, "Home_Kitchen": 1.0, "Beauty": 0.8, "Fitness": 0.9}
            views_mean = (
                50 + 
                marketing_spend * 8.0 + 
                (20 if is_weekend else 0)
            ) * category_traffic_weight[category] * month_factor * holiday_factor
            views = int(max(10, np.random.normal(views_mean, views_mean * 0.15)))
            
            # Clicks: base click through rate (CTR) + discount impact
            ctr_base = 0.08 + (discount_pct * 0.15)
            clicks = int(max(0, np.random.binomial(views, min(0.9, ctr_base))))
            
            # Conversion rate: base conversion (e.g. 0.02 to 0.08)
            # Higher discount increases conversion, higher price and shipping fee reduces it
            conv_base = 0.04 + (discount_pct * 0.12) - (price / 500.0) - (shipping_fee / 100.0)
            conv_rate = max(0.005, min(0.3, np.random.normal(conv_base, 0.01)))
            
            orders = int(max(0, np.random.binomial(clicks, conv_rate) if clicks > 0 else 0))
            
            # Revenue
            revenue = orders * price
            
            # COGS and Profit calculation
            # Profit = Revenue - Cost of Goods Sold - Marketing Spend - Shipping Subsidy (if shipping_fee is 0, we pay)
            cogs = orders * (base_price * cogs_pct)
            shipping_cost_to_us = orders * 6.0 if shipping_fee == 0.0 else orders * max(0.0, 6.0 - shipping_cost_to_us) if 'shipping_cost_to_us' in locals() else orders * max(0.0, 6.0 - shipping_fee)
            # wait, let's make sure shipping_cost_to_us is calculated correctly
            shipping_cost_to_us = orders * 6.0 if shipping_fee == 0.0 else orders * max(0.0, 6.0 - shipping_fee)
            profit = revenue - cogs - marketing_spend - shipping_cost_to_us
            
            # Retention Rate
            # Retention is higher with discounts, lower with high shipping fees
            retention = base_retention + (discount_pct * 0.25) - (shipping_fee / 80.0) + np.random.normal(0, 0.02)
            retention = max(0.01, min(0.95, retention))
            
            # Inventory
            # Starts at 200, drops with orders, replenishes to 200 every week
            day_of_year = date.timetuple().tm_yday
            if day_of_year % 7 == 1:
                inventory = np.random.choice([150, 200, 250])
            else:
                inventory = int(max(0, 180 - (orders * 3) + np.random.randint(-10, 10)))
            
            rows.append({
                "Date": date.strftime("%Y-%m-%d"),
                "Product_ID": prod_id,
                "Category": category,
                "Base_Price": round(base_price, 2),
                "Price": round(price, 2),
                "Discount_Pct": round(discount_pct, 4),
                "Shipping_Fee": round(shipping_fee, 2),
                "Marketing_Spend": round(marketing_spend, 2),
                "Inventory": inventory,
                "Views": views,
                "Clicks": clicks,
                "Orders": orders,
                "Revenue": round(revenue, 2),
                "Profit": round(profit, 2),
                "Conversion_Rate": round(conv_rate, 4),
                "Retention_Rate": round(retention, 4)
            })
            
    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Generated synthetic dataset with {len(df)} rows at {output_path}")
    return df

if __name__ == "__main__":
    out_dir = "data/raw/product_data.csv"
    generate_synthetic_data(out_dir)
