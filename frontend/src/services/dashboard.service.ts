import apiClient from '../api/client';
import { DashboardResponse, KpiData } from '../types';

export interface DashboardPayload {
  start_date: string | null;
  end_date: string | null;
  product_id: string | null;
  category: string | null;
}

export const getDashboardData = async (payload: DashboardPayload): Promise<DashboardResponse> => {
  const [kpis, channelData, campaignData] = await Promise.all([
    apiClient<KpiData>('/analytics/kpi', { method: 'POST', body: JSON.stringify(payload) }),
    apiClient<any>('/analytics/channel', { method: 'POST', body: JSON.stringify(payload) }),
    apiClient<any>('/analytics/campaign', { method: 'POST', body: JSON.stringify(payload) })
  ]);

  let inventoryData = null;
  if (payload.product_id) {
    inventoryData = await apiClient<any>('/analytics/inventory', {
      method: 'POST',
      body: JSON.stringify({
        product_id: payload.product_id,
        start_date: payload.start_date,
        end_date: payload.end_date
      })
    });
  }

  return {
    kpis,
    channelData,
    campaignData,
    inventoryData
  };
};
