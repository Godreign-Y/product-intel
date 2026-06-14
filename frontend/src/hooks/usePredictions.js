import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getPredictions } from '../services/predictions.service';
export function usePredictions() {
    const [selectedMetric, setSelectedMetric] = useState('Revenue');
    const [selectedTimeframe, setSelectedTimeframe] = useState('Monthly');
    const { data, isLoading, isError, error, refetch } = useQuery({
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
