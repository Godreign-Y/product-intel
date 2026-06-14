import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { getRecommendations, applyRecommendation } from '../services/recommendations.service';
export function useRecommendations() {
    const [filter, setFilter] = useState('All');
    const [localRecommendations, setLocalRecommendations] = useState([]);
    const { data: recommendations, isLoading, isError, error } = useQuery({
        queryKey: ['recommendations'],
        queryFn: getRecommendations,
        refetchOnWindowFocus: false,
    });
    useEffect(() => {
        if (recommendations) {
            setLocalRecommendations(recommendations);
        }
    }, [recommendations]);
    const applyMutation = useMutation({
        mutationFn: async (id) => {
            return applyRecommendation(id);
        },
        onSuccess: (updatedRec) => {
            setLocalRecommendations((prev) => prev.map((r) => (r.id === updatedRec.id ? updatedRec : r)));
        },
    });
    const filteredRecommendations = localRecommendations.filter((r) => {
        if (filter === 'All')
            return true;
        return r.category === filter;
    });
    const handleApply = (id) => {
        applyMutation.mutate(id);
    };
    return {
        recommendations: filteredRecommendations,
        allRecommendations: localRecommendations,
        filter,
        setFilter,
        isLoading,
        isError,
        error,
        isApplying: applyMutation.isPending,
        applyRecommendation: handleApply,
    };
}
