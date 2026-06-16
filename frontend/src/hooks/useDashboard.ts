import { useQuery } from '@tanstack/react-query';
import { getDashboardData, DashboardPayload } from '../services/dashboard.service';

export const useDashboard = (payload: DashboardPayload) => {
  return useQuery({
    queryKey: ['dashboard', payload.product_id, payload.category, payload.start_date, payload.end_date],
    queryFn: () => getDashboardData(payload),
    staleTime: 5 * 60 * 1000, // 5 minute cache
  });
};
