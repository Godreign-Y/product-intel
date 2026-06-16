import datetime
import pandas as pd
from typing import Dict, Any, List, Optional
from src.core.history.storage.models import Snapshot

class SnapshotBuilder:
    @staticmethod
    def build_snapshot(
        df_date: pd.DataFrame, 
        date_val: datetime.date, 
        prev_revenues: Optional[Dict[str, float]] = None
    ) -> Snapshot:
        """
        Builds a single Snapshot ORM object from a daily DataFrame slice.
        """
        # 1. Base Aggregations
        total_revenue = float(df_date["revenue"].sum())
        total_profit = float(df_date["profit"].sum())
        total_orders = int(df_date["orders"].sum())
        mean_conversion = float(df_date["conversion_rate"].mean())
        mean_retention = float(df_date["retention_rate"].mean())
        total_marketing = float(df_date["marketing_spend"].sum())
        total_inventory = int(df_date["inventory_available"].sum())
        avg_discount = float(df_date["discount_pct"].mean())
        avg_price = float(df_date["avg_selling_price"].mean())
        
        # 2. Product Rankings
        prod_revs = df_date.groupby("product_id")["revenue"].sum().to_dict()
        sorted_prods = sorted(prod_revs.items(), key=lambda x: x[1], reverse=True)
        
        top_products = [{"product_id": p, "revenue": round(r, 2)} for p, r in sorted_prods[:5]]
        worst_products = [{"product_id": p, "revenue": round(r, 2)} for p, r in sorted_prods[-5:]]
        
        # 3. Growth and Decline calculations
        largest_growth = []
        largest_decline = []
        
        if prev_revenues:
            growth_list = []
            for p, r in prod_revs.items():
                prev_r = prev_revenues.get(p, 0.0)
                diff = r - prev_r
                pct = (diff / prev_r * 100.0) if prev_r > 0 else 0.0
                growth_list.append({"product_id": p, "absolute_growth": round(diff, 2), "percentage": round(pct, 2)})
            
            # Sort growth
            sorted_growth = sorted(growth_list, key=lambda x: x["absolute_growth"], reverse=True)
            largest_growth = sorted_growth[:5]
            largest_decline = sorted_growth[-5:]
            
        # 4. Inventory alerts (stock <= 50 units)
        inv_alerts_df = df_date[df_date["inventory_available"] <= 50]
        inventory_alerts = [
            {"product_id": row["product_id"], "inventory": int(row["inventory_available"])}
            for _, row in inv_alerts_df.iterrows()
        ]
        
        # 5. Mix ratios
        channel_mix = {
            "Amazon": round(float(df_date["amazon_sales_pct"].mean()), 2),
            "Website": round(float(df_date["website_sales_pct"].mean()), 2),
            "Nykaa": round(float(df_date["nykaa_sales_pct"].mean()), 2),
            "MobileApp": round(float(df_date["mobile_app_sales_pct"].mean()), 2)
        }
        
        campaign_mix = {
            "Search": round(float(df_date["search_campaign_pct"].mean()), 2),
            "Social": round(float(df_date["social_campaign_pct"].mean()), 2),
            "Email": round(float(df_date["email_campaign_pct"].mean()), 2),
            "Affiliate": round(float(df_date["affiliate_campaign_pct"].mean()), 2)
        }
        
        traffic_mix = {
            "Google": round(float(df_date["google_source_pct"].mean()), 2),
            "Instagram": round(float(df_date["instagram_source_pct"].mean()), 2),
            "Facebook": round(float(df_date["facebook_source_pct"].mean()), 2),
            "Email": round(float(df_date["email_source_pct"].mean()), 2),
            "Organic": round(float(df_date["organic_source_pct"].mean()), 2),
            "Referral": round(float(df_date["referral_source_pct"].mean()), 2)
        }
        
        # 6. Structured Summary Narrative
        summary_text = (
            f"Daily business overview for {date_val.strftime('%Y-%m-%d')}. "
            f"Total platform revenue achieved: ${total_revenue:,.2f} on {total_orders:,} orders. "
            f"Average product price: ${avg_price:.2f} with a mean conversion rate of {mean_conversion * 100:.2f}%. "
            f"Top performing product was {top_products[0]['product_id'] if top_products else 'N/A'} (Revenue: ${top_products[0]['revenue']:,.2f}). "
            f"Active campaign channels were led by Search/Social mixes. "
        )
        if len(inventory_alerts) > 0:
            summary_text += f"Operationally, {len(inventory_alerts)} products raised inventory alert warnings (stock <= 50 units)."
        else:
            summary_text += "Operations were stable with zero stockout risks flagged."
            
        return Snapshot(
            snapshot_date=date_val,
            total_revenue=round(total_revenue, 2),
            total_profit=round(total_profit, 2),
            total_orders=total_orders,
            mean_conversion_rate=round(mean_conversion, 4),
            mean_retention_rate=round(mean_retention, 4),
            total_marketing_spend=round(total_marketing, 2),
            total_inventory=total_inventory,
            avg_discount_pct=round(avg_discount, 2),
            avg_price=round(avg_price, 2),
            top_products=top_products,
            worst_products=worst_products,
            largest_growth=largest_growth,
            largest_decline=largest_decline,
            inventory_alerts=inventory_alerts,
            channel_mix=channel_mix,
            campaign_mix=campaign_mix,
            traffic_mix=traffic_mix,
            summary=summary_text
        )
