import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getPredictions } from '../services/predictions.service';
import { PredictionsData } from '../types/predictions';

export function usePredictions() {
  const [selectedMetric, setSelectedMetric] = useState<string>('Revenue');
  const [selectedTimeframe, setSelectedTimeframe] = useState<string>('Monthly');

  const { data, isLoading, isError, error, refetch } = useQuery<PredictionsData, Error>({
    queryKey: ['predictions', selectedMetric, selectedTimeframe],
    queryFn: () => getPredictions(selectedMetric, selectedTimeframe),
    refetchOnWindowFocus: false,
  });

  return {
    predictionsData: data,
    selectedMetric,
    setSelectedMetric,
    selectedTimeframe,
    setSelectedTimeframe,
    isLoading,
    isError,
    error,
    refetch,
  };
}
