import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { getExperiments, simulateExperiment, createExperiment } from '../services/experiments.service';
export function useExperiments() {
    const [localExperiments, setLocalExperiments] = useState([]);
    const [activePreview, setActivePreview] = useState(null);
    const { data: experiments, isLoading, isError, error } = useQuery({
        queryKey: ['experiments'],
        queryFn: getExperiments,
        refetchOnWindowFocus: false,
    });
    useEffect(() => {
        if (experiments) {
            setLocalExperiments(experiments);
        }
    }, [experiments]);
    // Simulate Mutation
    const simulateMutation = useMutation({
        mutationFn: async ({ name, objective, hypothesis, primaryMetric, type, variables, }) => {
            return simulateExperiment(name, objective, hypothesis, primaryMetric, type, variables);
        },
        onSuccess: (previewData, variables) => {
            setActivePreview(previewData);
        },
    });
    // Launch/Create Experiment Mutation
    const createMutation = useMutation({
        mutationFn: async (newExp) => {
            return createExperiment(newExp);
        },
        onSuccess: (savedExp) => {
            setLocalExperiments((prev) => [savedExp, ...prev]);
        }
    });
    const handleCreateExperiment = (newExp) => {
        const experiment = {
            ...newExp,
            id: `exp_${Date.now()}`,
            status: 'Running', // default to running on launch
            createdAt: new Date().toISOString(),
            simulationPreview: activePreview || undefined,
        };
        createMutation.mutate(experiment);
        // Clear active preview after saving
        setActivePreview(null);
    };
    const handleSimulate = (name, objective, hypothesis, primaryMetric, type, variables) => {
        simulateMutation.mutate({ name, objective, hypothesis, primaryMetric, type, variables });
    };
    return {
        experiments: localExperiments,
        activePreview,
        isLoading,
        isError,
        error,
        isSimulating: simulateMutation.isPending,
        isSimulateError: simulateMutation.isError,
        simulateError: simulateMutation.error,
        runSimulation: handleSimulate,
        createExperiment: handleCreateExperiment,
        clearPreview: () => setActivePreview(null),
    };
}
