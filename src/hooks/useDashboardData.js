import { useQuery } from '@tanstack/react-query';
import { getDashboardData } from '../services/dashboard.service';
export function useDashboardData() {
    return useQuery({
        queryKey: ['dashboardData'],
        queryFn: getDashboardData,
        refetchOnWindowFocus: false,
        staleTime: 5 * 60 * 1000, // 5 minutes
    });
}
