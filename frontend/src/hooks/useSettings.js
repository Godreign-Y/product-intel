import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getSettings, updateSettings, testFastApiConnection } from '../services/settings.service';
export function useSettings() {
    const queryClient = useQueryClient();
    const [localSettings, setLocalSettings] = useState(null);
    const [testResult, setTestResult] = useState('idle');
    const { data: settings, isLoading, isError, error } = useQuery({
        queryKey: ['settings'],
        queryFn: getSettings,
        refetchOnWindowFocus: false,
    });
    useEffect(() => {
        if (settings) {
            setLocalSettings(settings);
        }
    }, [settings]);
    const updateMutation = useMutation({
        mutationFn: async (updated) => {
            return updateSettings(updated);
        },
        onSuccess: (updated) => {
            setLocalSettings(updated);
            queryClient.invalidateQueries({ queryKey: ['settings'] });
            // Clear out general cache if FastAPI mode was toggled so other queries fetch from real FastAPI or mock
            queryClient.resetQueries();
        },
    });
    const saveSettings = (updated) => {
        updateMutation.mutate(updated);
    };
    const runTestConnection = async (url, apiKey) => {
        setTestResult('testing');
        const result = await testFastApiConnection(url, apiKey);
        setTestResult(result);
        // Update db status in settings if connected
        if (localSettings) {
            const updatedSettings = {
                ...localSettings,
                dbStatus: result,
            };
            setLocalSettings(updatedSettings);
            saveSettings(updatedSettings);
        }
    };
    return {
        settings: localSettings,
        isLoading,
        isError,
        error,
        isSaving: updateMutation.isPending,
        testStatus: testResult,
        saveSettings,
        testConnection: runTestConnection,
    };
}
