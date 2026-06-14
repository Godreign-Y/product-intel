import { request } from '../utils/api-client';
import { PredictionsData } from '../types/predictions';
import { mockPredictionsData } from '../mocks/predictions.mock';

export async function getPredictions(metric: string, timeframe: string): Promise<PredictionsData> {
  // Translate UI metric selectors to mock keys
  const lookupKey = metric.toLowerCase().replace(/[^a-z]/g, '');
  const data = mockPredictionsData[lookupKey] || mockPredictionsData.revenue;
  
  // Custom endpoint formatting
  return request<PredictionsData>(
    `/api/predictions?metric=${metric}&timeframe=${timeframe}`,
    {
      ...data,
      metric,
      timeframe,
    }
  );
}
