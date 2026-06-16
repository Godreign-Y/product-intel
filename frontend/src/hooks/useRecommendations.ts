import { useQuery } from '@tanstack/react-query';
import { getTopAnomalies, getAnomalyDetails } from '../services/recommendations.service';

export const useTopAnomalies = (targetDate: string, kpi: string) => {
  return useQuery({
    queryKey: ['topAnomalies', targetDate, kpi],
    queryFn: () => getTopAnomalies(targetDate, kpi),
    staleTime: 5 * 60 * 1000, // 5 minute cache
  });
};

export const useAnomalyDetails = (productId: string | null, targetDate: string, kpi: string) => {
  return useQuery({
    queryKey: ['anomalyDetails', productId, targetDate, kpi],
    queryFn: () => getAnomalyDetails(productId as string, targetDate, kpi),
    enabled: !!productId,
    staleTime: 5 * 60 * 1000, // 5 minute cache
  });
};
