import { PredictionsData } from '../types/predictions';

export const mockPredictionsData: Record<string, PredictionsData> = {
  revenue: {
    metric: 'Revenue',
    timeframe: 'Monthly',
    forecastPoints: [
      { date: 'Apr \'26', actual: 6200000 },
      { date: 'May \'26', actual: 6800000 },
      { date: 'Jun \'26', actual: 7450000, forecast: 7450000, confidenceLower: 7450000, confidenceUpper: 7450000 },
      { date: 'Jul \'26', forecast: 7800000, confidenceLower: 7200000, confidenceUpper: 8400000 },
      { date: 'Aug \'26', forecast: 8100000, confidenceLower: 7300000, confidenceUpper: 8900000 },
      { date: 'Sep \'26', forecast: 8500000, confidenceLower: 7500000, confidenceUpper: 9500000 },
    ],
    summaryTable: [
      { metric: 'Revenue', nextPeriodForecast: '$7.80M', projectedChangePercent: 10.4, isPositive: true, confidence: 78 },
      { metric: 'Orders', nextPeriodForecast: '22,890', projectedChangePercent: 11.2, isPositive: true, confidence: 78 },
      { metric: 'Conversion Rate', nextPeriodForecast: '3.72%', projectedChangePercent: 2.8, isPositive: true, confidence: 72 },
      { metric: 'AOV', nextPeriodForecast: '$129.3', projectedChangePercent: 3.8, isPositive: true, confidence: 75 },
      { metric: 'Profit', nextPeriodForecast: '$912K', projectedChangePercent: 14.2, isPositive: true, confidence: 80 },
    ],
  },
  orders: {
    metric: 'Orders',
    timeframe: 'Monthly',
    forecastPoints: [
      { date: 'Apr \'26', actual: 17200 },
      { date: 'May \'26', actual: 18500 },
      { date: 'Jun \'26', actual: 20580, forecast: 20580, confidenceLower: 20580, confidenceUpper: 20580 },
      { date: 'Jul \'26', forecast: 22890, confidenceLower: 21500, confidenceUpper: 24280 },
      { date: 'Aug \'26', forecast: 24100, confidenceLower: 22200, confidenceUpper: 26000 },
      { date: 'Sep \'26', forecast: 25800, confidenceLower: 23100, confidenceUpper: 28500 },
    ],
    summaryTable: [
      { metric: 'Revenue', nextPeriodForecast: '$7.80M', projectedChangePercent: 10.4, isPositive: true, confidence: 78 },
      { metric: 'Orders', nextPeriodForecast: '22,890', projectedChangePercent: 11.2, isPositive: true, confidence: 78 },
      { metric: 'Conversion Rate', nextPeriodForecast: '3.72%', projectedChangePercent: 2.8, isPositive: true, confidence: 72 },
      { metric: 'AOV', nextPeriodForecast: '$129.3', projectedChangePercent: 3.8, isPositive: true, confidence: 75 },
      { metric: 'Profit', nextPeriodForecast: '$912K', projectedChangePercent: 14.2, isPositive: true, confidence: 80 },
    ],
  },
  conversionRate: {
    metric: 'Conversion Rate',
    timeframe: 'Monthly',
    forecastPoints: [
      { date: 'Apr \'26', actual: 3.42 },
      { date: 'May \'26', actual: 3.55 },
      { date: 'Jun \'26', actual: 3.62, forecast: 3.62, confidenceLower: 3.62, confidenceUpper: 3.62 },
      { date: 'Jul \'26', forecast: 3.72, confidenceLower: 3.50, confidenceUpper: 3.94 },
      { date: 'Aug \'26', forecast: 3.78, confidenceLower: 3.48, confidenceUpper: 4.08 },
      { date: 'Sep \'26', forecast: 3.85, confidenceLower: 3.52, confidenceUpper: 4.18 },
    ],
    summaryTable: [
      { metric: 'Revenue', nextPeriodForecast: '$7.80M', projectedChangePercent: 10.4, isPositive: true, confidence: 78 },
      { metric: 'Orders', nextPeriodForecast: '22,890', projectedChangePercent: 11.2, isPositive: true, confidence: 78 },
      { metric: 'Conversion Rate', nextPeriodForecast: '3.72%', projectedChangePercent: 2.8, isPositive: true, confidence: 72 },
      { metric: 'AOV', nextPeriodForecast: '$129.3', projectedChangePercent: 3.8, isPositive: true, confidence: 75 },
      { metric: 'Profit', nextPeriodForecast: '$912K', projectedChangePercent: 14.2, isPositive: true, confidence: 80 },
    ],
  },
  aov: {
    metric: 'AOV',
    timeframe: 'Monthly',
    forecastPoints: [
      { date: 'Apr \'26', actual: 118.2 },
      { date: 'May \'26', actual: 122.4 },
      { date: 'Jun \'26', actual: 124.6, forecast: 124.6, confidenceLower: 124.6, confidenceUpper: 124.6 },
      { date: 'Jul \'26', forecast: 129.3, confidenceLower: 122.0, confidenceUpper: 136.0 },
      { date: 'Aug \'26', forecast: 132.8, confidenceLower: 124.0, confidenceUpper: 141.0 },
      { date: 'Sep \'26', forecast: 136.5, confidenceLower: 125.0, confidenceUpper: 148.0 },
    ],
    summaryTable: [
      { metric: 'Revenue', nextPeriodForecast: '$7.80M', projectedChangePercent: 10.4, isPositive: true, confidence: 78 },
      { metric: 'Orders', nextPeriodForecast: '22,890', projectedChangePercent: 11.2, isPositive: true, confidence: 78 },
      { metric: 'Conversion Rate', nextPeriodForecast: '3.72%', projectedChangePercent: 2.8, isPositive: true, confidence: 72 },
      { metric: 'AOV', nextPeriodForecast: '$129.3', projectedChangePercent: 3.8, isPositive: true, confidence: 75 },
      { metric: 'Profit', nextPeriodForecast: '$912K', projectedChangePercent: 14.2, isPositive: true, confidence: 80 },
    ],
  },
  profit: {
    metric: 'Profit',
    timeframe: 'Monthly',
    forecastPoints: [
      { date: 'Apr \'26', actual: 720000 },
      { date: 'May \'26', actual: 790000 },
      { date: 'Jun \'26', actual: 842000, forecast: 842000, confidenceLower: 842000, confidenceUpper: 842000 },
      { date: 'Jul \'26', forecast: 912000, confidenceLower: 850000, confidenceUpper: 980000 },
      { date: 'Aug \'26', forecast: 955000, confidenceLower: 870000, confidenceUpper: 1040000 },
      { date: 'Sep \'26', forecast: 1010000, confidenceLower: 890000, confidenceUpper: 1130000 },
    ],
    summaryTable: [
      { metric: 'Revenue', nextPeriodForecast: '$7.80M', projectedChangePercent: 10.4, isPositive: true, confidence: 78 },
      { metric: 'Orders', nextPeriodForecast: '22,890', projectedChangePercent: 11.2, isPositive: true, confidence: 78 },
      { metric: 'Conversion Rate', nextPeriodForecast: '3.72%', projectedChangePercent: 2.8, isPositive: true, confidence: 72 },
      { metric: 'AOV', nextPeriodForecast: '$129.3', projectedChangePercent: 3.8, isPositive: true, confidence: 75 },
      { metric: 'Profit', nextPeriodForecast: '$912K', projectedChangePercent: 14.2, isPositive: true, confidence: 80 },
    ],
  },
};
export const defaultForecastMetric = 'revenue';
