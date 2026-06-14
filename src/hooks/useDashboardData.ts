import { useQuery } from '@tanstack/react-query';
import { getDashboardData } from '../services/dashboard.service';
import { DashboardData } from '../types/dashboard';

export function useDashboardData() {
  return useQuery<DashboardData, Error>({
    queryKey: ['dashboardData'],
    queryFn: getDashboardData,
    refetchOnWindowFocus: false,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
