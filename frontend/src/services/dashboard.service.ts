import { request } from '../utils/api-client';
import { DashboardData } from '../types/dashboard';
import { mockDashboardData } from '../mocks/dashboard.mock';

export async function getDashboardData(): Promise<DashboardData> {
  return request<DashboardData>('/api/dashboard', mockDashboardData);
}
