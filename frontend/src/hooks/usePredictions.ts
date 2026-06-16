import { useQuery } from '@tanstack/react-query';
import { getPredictionsData, TrendPayload } from '../services/predictions.service';

export const usePredictions = (payload: TrendPayload) => {
  return useQuery({
    queryKey: ['predictions', payload.product_id, payload.category, payload.start_date, payload.end_date, payload.metric, payload.granularity],
    queryFn: () => getPredictionsData(payload),
    staleTime: 5 * 60 * 1000, // 5 minute cache
  });
};
