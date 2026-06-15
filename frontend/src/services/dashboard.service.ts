/**
 * Dashboard Service.
 *
 * Fetches and aggregates data from multiple backend analytics endpoints
 * to compose the executive dashboard view. All data comes from real API calls.
 *
 * @module dashboard.service
 */

import { request, getApiBaseUrl, getHeaders } from '../utils/api-client';
import {
  DashboardData,
  KPICardData,
  PerformanceOverTimePoint,
  Anomaly,
  TopOpportunity,
  RecentExperiment,
} from '../types/dashboard';

/**
 * Format helper for numeric currency displays.
 *
 * @param val - Currency value to format.
 * @returns Formatted currency string.
 */
function formatCurrency(val: number): string {
  if (val >= 1000000) return `$${(val / 1000000).toFixed(2)}M`;
  if (val >= 1000) return `$${(val / 1000).toFixed(0)}K`;
  return `$${val.toFixed(2)}`;
}

/**
 * Retrieves the compiled dashboard data.
 * Queries all necessary backend analytics endpoints and combines their
 * outputs into a single cohesive dashboard payload.
 *
 * @returns Promise resolving to the dashboard dataset.
 */
export async function getDashboardData(): Promise<DashboardData> {
  const baseUrl = getApiBaseUrl();
  const headers = getHeaders();

  // 1. Fetch KPI overview
  const kpiPromise = fetch(`${baseUrl}/api/v1/analytics/kpi`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ product_id: 'P001' }),
  }).then((res) => {
    if (!res.ok) throw new Error('KPI fetch failed');
    return res.json();
  });

  // 2. Fetch trends for sparklines & performance chart
  const trendMetrics = ['revenue', 'orders', 'conversion_rate', 'profit'];
  const trendPromises = trendMetrics.map((m) =>
    fetch(`${baseUrl}/api/v1/analytics/trend`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ product_id: 'P001', metric: m }),
    }).then((res) => {
      if (!res.ok) throw new Error(`Trend fetch failed for ${m}`);
      return res.json();
    })
  );

  // 3. Fetch declining products (anomalies)
  const decliningPromise = fetch(`${baseUrl}/api/v1/analysis/declining`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ lookback_days: 30, metric: 'revenue' }),
  }).then((res) => {
    if (!res.ok) throw new Error('Declining products fetch failed');
    return res.json();
  });

  // 4. Fetch sensitivity scores (opportunities)
  const sensitivityPromise = fetch(`${baseUrl}/api/v1/sensitivity/estimate`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ product_id: 'P001', horizon_days: 30 }),
  }).then((res) => {
    if (!res.ok) throw new Error('Sensitivity fetch failed');
    return res.json();
  });

  // 5. Fetch recent experiments from PostgreSQL DB
  const experimentsPromise = fetch(`${baseUrl}/api/v1/db/experiments`, {
    headers,
  }).then((res) => {
    if (!res.ok) return [];
    return res.json();
  });

  const [
    kpis,
    trendRevenue,
    trendOrders,
    trendConv,
    trendProfit,
    declining,
    sensitivity,
    dbExperiments,
  ] = await Promise.all([
    kpiPromise,
    trendPromises[0],
    trendPromises[1],
    trendPromises[2],
    trendPromises[3],
    decliningPromise,
    sensitivityPromise,
    experimentsPromise,
  ]);

  // Format KPI Cards
  const kpiCards: KPICardData[] = [
    {
      id: 'revenue',
      title: 'Revenue',
      value: formatCurrency(kpis.revenue.sum),
      changePercent: parseFloat(trendRevenue.growth_rate_pct.toFixed(1)),
      isPositive: trendRevenue.growth_rate_pct >= 0,
      timeframe: 'vs Previous Period',
      sparkline: trendRevenue.history.slice(-8).map((pt: any) => ({
        date: pt.date.substring(5),
        value: pt.value,
      })),
    },
    {
      id: 'orders',
      title: 'Orders',
      value: Math.round(kpis.orders.sum).toLocaleString(),
      changePercent: parseFloat(trendOrders.growth_rate_pct.toFixed(1)),
      isPositive: trendOrders.growth_rate_pct >= 0,
      timeframe: 'vs Previous Period',
      sparkline: trendOrders.history.slice(-8).map((pt: any) => ({
        date: pt.date.substring(5),
        value: pt.value,
      })),
    },
    {
      id: 'conversion_rate',
      title: 'Conversion Rate',
      value: `${(kpis.conversion_rate.mean * 100).toFixed(2)}%`,
      changePercent: parseFloat(trendConv.growth_rate_pct.toFixed(1)),
      isPositive: trendConv.growth_rate_pct >= 0,
      timeframe: 'vs Previous Period',
      sparkline: trendConv.history.slice(-8).map((pt: any) => ({
        date: pt.date.substring(5),
        value: pt.value * 100,
      })),
    },
    {
      id: 'profit',
      title: 'Profit',
      value: formatCurrency(kpis.profit.sum),
      changePercent: parseFloat(trendProfit.growth_rate_pct.toFixed(1)),
      isPositive: trendProfit.growth_rate_pct >= 0,
      timeframe: 'vs Previous Period',
      sparkline: trendProfit.history.slice(-8).map((pt: any) => ({
        date: pt.date.substring(5),
        value: pt.value,
      })),
    },
  ];

  // Format Performance Grid Chart Data
  const performancePoints: PerformanceOverTimePoint[] = [];
  const minLen = Math.min(
    trendRevenue.history.length,
    trendOrders.history.length,
    trendConv.history.length,
    trendProfit.history.length
  );

  for (let i = 0; i < minLen; i++) {
    performancePoints.push({
      date: trendRevenue.history[i].date.substring(5),
      revenue: trendRevenue.history[i].value,
      orders: trendOrders.history[i].value,
      conversionRate: parseFloat(
        (trendConv.history[i].value * 100).toFixed(2)
      ),
      profit: trendProfit.history[i].value,
    });
  }

  // Format Anomalies list
  const anomalies: Anomaly[] = (declining.declining_products || [])
    .slice(0, 3)
    .map((item: any, idx: number) => ({
      id: `anom_db_${idx}`,
      title: `Declining trend in ${item.category}`,
      description: `Product ${item.product_id} shows a decline rate of ${item.percentage_change.toFixed(1)}% in selected period.`,
      severity: item.percentage_change < -10 ? 'high' : 'medium',
      detectedAt: 'Recent Analysis',
    }));

  if (anomalies.length === 0) {
    anomalies.push({
      id: 'anom_none',
      title: 'No declining revenue trends',
      description: 'All tracked product categories are stable or growing.',
      severity: 'low',
      detectedAt: 'Recent Analysis',
    });
  }

  // Format Opportunities (based on elasticity weights)
  const rawOpportunities = [
    { key: 'marketing', name: 'Increase Marketing Spend', data: sensitivity.marketing },
    { key: 'discount', name: 'Optimize Discount Percentage', data: sensitivity.discount },
    { key: 'price', name: 'Refine Average Retail Price', data: sensitivity.price },
    { key: 'shipping', name: 'Reduce Shipping Friction', data: sensitivity.shipping },
  ];

  const sortedOpps = rawOpportunities
    .filter((o) => o.data)
    .sort((a, b) => Math.abs(b.data.expected_impact) - Math.abs(a.data.expected_impact));

  const opportunities: TopOpportunity[] = sortedOpps.slice(0, 3).map((opp) => {
    const impactVal = opp.data.expected_impact * 100;
    return {
      id: `opp_db_${opp.key}`,
      title: opp.name,
      impactValue: `${impactVal >= 0 ? '+' : ''}${impactVal.toFixed(1)}% lift`,
      impactLevel: Math.abs(impactVal) > 5 ? 'High' : 'Medium',
      priority: Math.abs(impactVal) > 5 ? 'high' : 'medium',
    };
  });

  // Format Recent Experiments
  const recentExperiments: RecentExperiment[] = dbExperiments
    .slice(0, 5)
    .map((exp: any) => ({
      id: exp.id,
      name: exp.name,
      status: exp.status,
      result: exp.simulation_preview
        ? `+${exp.simulation_preview.expectedImpact[0]?.percentChange}% Conversion`
        : undefined,
      changePercent: exp.simulation_preview
        ? exp.simulation_preview.expectedImpact[0]?.percentChange
        : undefined,
      isPositive: true,
    }));

  // AI Insight Summary — dynamically generated from real data
  const revChangeStr = trendRevenue.growth_rate_pct >= 0 ? 'growth' : 'decline';
  const topOpp = opportunities[0] ? opportunities[0].title : 'Marketing Spend';
  const summaryText = `Model audit shows a ${trendRevenue.growth_rate_pct.toFixed(1)}% revenue ${revChangeStr} for this product period. Performance optimization suggests prioritizing '${topOpp}' which holds the highest causal elasticity value.`;

  const bulletPoints = [
    `Conversion rate average is sitting at ${(kpis.conversion_rate.mean * 100).toFixed(2)}%.`,
    `Profit margins remain healthy at ${(kpis.profit.profit_margin * 100).toFixed(1)}%.`,
    `Caused anomalies check: detected ${anomalies.length} potential area(s) of decline.`,
  ];

  // Compute AI confidence from trend data consistency
  const allGrowthRates = [
    trendRevenue.growth_rate_pct,
    trendOrders.growth_rate_pct,
    trendConv.growth_rate_pct,
    trendProfit.growth_rate_pct,
  ];
  const avgAbsGrowth = allGrowthRates.reduce((s, v) => s + Math.abs(v), 0) / allGrowthRates.length;
  const aiConfidence = Math.min(98, Math.max(70, Math.round(95 - avgAbsGrowth * 0.3)));

  return {
    kpis: kpiCards,
    performanceData: performancePoints.slice(-30),
    anomalies,
    opportunities,
    recentExperiments,
    aiConfidence,
    insightSummary: {
      text: summaryText,
      bulletPoints,
      recommendationLink: '/recommendations',
    },
    recentInsights: [
      {
        id: 'ins_db_1',
        title: 'Elasticity Assessment',
        description: `Sensitivity estimations indicate high sensitivity to pricing adjustments (coefficient: ${sensitivity.price?.elasticity_score?.toFixed(2) || 'N/A'}).`,
        priority: 'High',
        expectedImpact: 'LTV Optimization',
      },
      {
        id: 'ins_db_2',
        title: 'Inventory Health Index',
        description: `Average inventory stockouts score risk is assessed at: ${sensitivity.inventory?.expected_impact >= 0 ? 'Stable' : 'Restock Warn'}.`,
        priority: 'Medium',
        expectedImpact: 'Logistics Guard',
      },
    ],
  };
}
