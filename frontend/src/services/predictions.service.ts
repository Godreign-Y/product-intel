import apiClient from '../api/client';
import { PredictionResponse, TrendData } from '../types';

export interface TrendPayload {
  start_date: string | null;
  end_date: string | null;
  product_id: string | null;
  category: string | null;
  metric: string;
  granularity: string;
}

export const getPredictionsData = async (payload: TrendPayload): Promise<PredictionResponse> => {
  const data = await apiClient<TrendData>('/analytics/trend', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
  
  return { data };
};
