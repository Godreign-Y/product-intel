export interface SparklinePoint {
  date: string;
  value: number;
}

export interface KPICardData {
  id: string;
  title: string;
  value: string;
  changePercent: number;
  isPositive: boolean;
  timeframe: string;
  sparkline: SparklinePoint[];
}

export interface PerformanceOverTimePoint {
  date: string;
  revenue: number;
  orders: number;
  conversionRate: number;
  profit: number;
}

export interface Anomaly {
  id: string;
  title: string;
  description: string;
  severity: 'high' | 'medium' | 'low';
  detectedAt: string;
}

export interface TopOpportunity {
  id: string;
  title: string;
  impactValue: string;
  impactLevel: 'High' | 'Medium' | 'Low';
  priority: 'high' | 'medium' | 'low';
}

export interface RecentExperiment {
  id: string;
  name: string;
  status: 'Running' | 'Completed' | 'Draft';
  result?: string;
  changePercent?: number;
  isPositive?: boolean;
}

export interface AIInsightSummary {
  text: string;
  bulletPoints: string[];
  recommendationLink: string;
}

export interface DashboardData {
  kpis: KPICardData[];
  performanceData: PerformanceOverTimePoint[];
  anomalies: Anomaly[];
  opportunities: TopOpportunity[];
  recentExperiments: RecentExperiment[];
  insightSummary: AIInsightSummary;
}
