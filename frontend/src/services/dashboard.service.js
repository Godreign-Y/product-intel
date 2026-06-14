import { request } from '../utils/api-client';
import { mockDashboardData } from '../mocks/dashboard.mock';
export async function getDashboardData() {
    return request('/api/dashboard', mockDashboardData);
}
