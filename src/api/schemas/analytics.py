from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional

class AnalyticsRequest(BaseModel):
    start_date: Optional[str] = Field(default=None, description="Start date in format YYYY-MM-DD")
    end_date: Optional[str] = Field(default=None, description="End date in format YYYY-MM-DD")
    product_id: Optional[str] = Field(default=None, description="Optional product ID filter")
    category: Optional[str] = Field(default=None, description="Optional category filter")

class TrendRequest(AnalyticsRequest):
    metric: str = Field(default="revenue", description="Metric to analyze, e.g. revenue, profit, orders, traffic")

class ProductAnalyticsRequest(BaseModel):
    product_id: str = Field(..., description="Product ID, e.g. P001")
    start_date: Optional[str] = Field(default=None, description="Start date in format YYYY-MM-DD")
    end_date: Optional[str] = Field(default=None, description="End date in format YYYY-MM-DD")

# KPI Summary schemas
class KPIMetricSumAvg(BaseModel):
    sum: float
    daily_avg: float

class KPIMetricProfit(KPIMetricSumAvg):
    profit_margin: float

class KPIMetricMean(BaseModel):
    mean: float

class KPISummaryResponse(BaseModel):
    revenue: KPIMetricSumAvg
    profit: KPIMetricProfit
    orders: KPIMetricSumAvg
    traffic: KPIMetricSumAvg
    conversion_rate: KPIMetricMean
    retention_rate: KPIMetricMean
    marketing_spend: KPIMetricSumAvg
    days_in_period: int

# Trend Schemas
class TrendPoint(BaseModel):
    date: str
    value: float

class TrendResponse(BaseModel):
    metric: str
    direction: str
    slope: float
    r_squared: float
    p_value: float
    growth_rate_pct: float
    history: List[TrendPoint]

# Benchmark Schemas
class BenchmarkDetail(BaseModel):
    product_value: float
    category_benchmark: float
    global_benchmark: float
    pct_vs_category: float
    pct_vs_global: float

class BenchmarkResponse(BaseModel):
    product_id: str
    category: str
    comparisons: Dict[str, BenchmarkDetail]

# Seasonality Schemas
class DailySeasonalityDetail(BaseModel):
    revenue: float
    orders: float

class WeekendVsWeekdayDetail(BaseModel):
    weekday: DailySeasonalityDetail
    weekend: DailySeasonalityDetail
    revenue_lift_pct: float
    orders_lift_pct: float

class SeasonalityResponse(BaseModel):
    day_of_week_avg: Dict[str, DailySeasonalityDetail]
    weekend_vs_weekday: WeekendVsWeekdayDetail
    monthly_avg: Dict[str, DailySeasonalityDetail]

# Channel Schemas
class TopChannelDetail(BaseModel):
    channel: str
    share: float

class ChannelResponse(BaseModel):
    channel_mix: Dict[str, float]
    estimated_revenue: Dict[str, float]
    estimated_orders: Dict[str, float]
    top_channel: TopChannelDetail

# Campaign Schemas
class TopCampaignDetail(BaseModel):
    campaign: str
    share: float

class GeneralMarketingMetrics(BaseModel):
    avg_ctr: float
    avg_roas: float

class CampaignResponse(BaseModel):
    campaign_mix: Dict[str, float]
    estimated_spend: Dict[str, float]
    top_campaign_type: TopCampaignDetail
    general_metrics: GeneralMarketingMetrics

# Inventory Schemas
class InventoryResponse(BaseModel):
    product_id: str
    current_stock: int
    average_stock: float
    estimated_days_of_stock: float
    stockout_risk: str
    inventory_ratio_avg: float

# Customer Schemas
class ActiveUsersDetail(BaseModel):
    mean: float
    max: int

class CustomerResponse(BaseModel):
    average_ltv: float
    active_users: ActiveUsersDetail
    retention_rate_avg: float
    age_group_distribution: Dict[str, float]

# Marketing Schemas
class MarketingResponse(BaseModel):
    total_marketing_spend: float
    average_roas: float
    average_ctr: float
    marketing_spend_to_revenue_ratio: float
    spend_revenue_correlation: float

# Pricing Schemas
class DiscountBucketDetail(BaseModel):
    average_price: float
    average_orders: float
    average_revenue: float
    average_conversion_rate: float
    sample_count: int

class PricingResponse(BaseModel):
    average_price: float
    average_discount: float
    discount_buckets_performance: Dict[str, DiscountBucketDetail]
    price_elasticity_estimate: float
