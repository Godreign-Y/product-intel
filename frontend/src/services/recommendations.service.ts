import apiClient from '../api/client';
import { RecommendationResponse } from '../types';

export const getTopAnomalies = async (targetDate: string, kpi: string) => {
  return apiClient<any>('/anomaly/top-products', {
    method: 'POST',
    body: JSON.stringify({ target_date: targetDate, kpi, limit: 25 }),
  });
};

export const getAnomalyDetails = async (productId: string, targetDate: string, kpi: string) => {
  return apiClient<any>('/anomaly/detect', {
    method: 'POST',
    body: JSON.stringify({ product_id: productId, target_date: targetDate, kpi })
  });
};

export const getRecommendations = async (productId: string | null, targetDate: string, kpi: string): Promise<RecommendationResponse> => {
  const report = await getTopAnomalies(targetDate, kpi);
  
  let details = null;
  const targetProduct = productId || (report?.top_10_critical_products?.length > 0 ? report.top_10_critical_products[0].product_id : null);
  
  if (targetProduct) {
    details = await getAnomalyDetails(targetProduct, targetDate, kpi);
  }

  return { report, details };
};
