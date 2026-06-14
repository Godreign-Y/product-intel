import pandas as pd
from typing import Dict, Any, Optional

from src.core.analytics.kpi import analyze_kpis
from src.core.analytics.trend import analyze_trends
from src.core.analytics.benchmark import analyze_benchmarks
from src.core.analytics.seasonality import analyze_seasonality
from src.core.analytics.channel import analyze_channels
from src.core.analytics.campaign import analyze_campaigns
from src.core.analytics.inventory import analyze_inventory
from src.core.analytics.customer import analyze_customers
from src.core.analytics.marketing import analyze_marketing
from src.core.analytics.pricing import analyze_pricing

class AnalyticsEngine:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def get_kpis(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        product_id: Optional[str] = None,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        return analyze_kpis(self.df, start_date=start_date, end_date=end_date, product_id=product_id, category=category)

    def get_trends(
        self,
        metric: str = "revenue",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        product_id: Optional[str] = None
    ) -> Dict[str, Any]:
        return analyze_trends(self.df, metric=metric, start_date=start_date, end_date=end_date, product_id=product_id)

    def get_benchmarks(
        self,
        product_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        return analyze_benchmarks(self.df, product_id=product_id, start_date=start_date, end_date=end_date)

    def get_seasonality(
        self,
        product_id: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        return analyze_seasonality(self.df, product_id=product_id, category=category, start_date=start_date, end_date=end_date)

    def get_channels(
        self,
        product_id: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        return analyze_channels(self.df, product_id=product_id, category=category, start_date=start_date, end_date=end_date)

    def get_campaigns(
        self,
        product_id: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        return analyze_campaigns(self.df, product_id=product_id, category=category, start_date=start_date, end_date=end_date)

    def get_inventory(
        self,
        product_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        return analyze_inventory(self.df, product_id=product_id, start_date=start_date, end_date=end_date)

    def get_customers(
        self,
        product_id: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        return analyze_customers(self.df, product_id=product_id, category=category, start_date=start_date, end_date=end_date)

    def get_marketing(
        self,
        product_id: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        return analyze_marketing(self.df, product_id=product_id, category=category, start_date=start_date, end_date=end_date)

    def get_pricing(
        self,
        product_id: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        return analyze_pricing(self.df, product_id=product_id, category=category, start_date=start_date, end_date=end_date)
