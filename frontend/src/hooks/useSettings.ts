import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getSettings, updateSettings, testFastApiConnection } from '../services/settings.service';
import { SystemSettings } from '../types/settings';

export function useSettings() {
  const queryClient = useQueryClient();
  const [localSettings, setLocalSettings] = useState<SystemSettings | null>(null);
  const [testResult, setTestResult] = useState<'idle' | 'testing' | 'Connected' | 'Disconnected'>('idle');

  const { data: settings, isLoading, isError, error } = useQuery<SystemSettings, Error>({
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
    mutationFn: async (updated: SystemSettings) => {
      return updateSettings(updated);
    },
    onSuccess: (updated) => {
      setLocalSettings(updated);
      queryClient.invalidateQueries({ queryKey: ['settings'] });
      // Clear out general cache if FastAPI mode was toggled so other queries fetch from real FastAPI or mock
      queryClient.resetQueries();
    },
  });

  const saveSettings = (updated: SystemSettings) => {
    updateMutation.mutate(updated);
  };

  const runTestConnection = async (url: string, apiKey: string) => {
    setTestResult('testing');
    const result = await testFastApiConnection(url, apiKey);
    setTestResult(result);
    
    // Update db status in settings if connected
    if (localSettings) {
      const updatedSettings: SystemSettings = {
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
