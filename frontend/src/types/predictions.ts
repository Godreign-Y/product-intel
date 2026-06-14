export interface MetricForecastPoint {
  date: string;
  actual?: number;
  forecast?: number;
  confidenceLower?: number;
  confidenceUpper?: number;
}

export interface ForecastMetricRow {
  metric: string;
  nextPeriodForecast: string;
  projectedChangePercent: number;
  isPositive: boolean;
  confidence: number;
}

export interface SHAPDriver {
  name: string;
  weight: number;
}

export interface AccuracyIndicators {
  confidence: string;
  mae: string;
  horizon: string;
}

export interface PredictionsData {
  metric: string;
  timeframe: string;
  forecastPoints: MetricForecastPoint[];
  summaryTable: ForecastMetricRow[];
  shapDrivers?: SHAPDriver[];
  explanationText?: string;
  accuracyIndicators?: AccuracyIndicators;
}
