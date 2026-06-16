import apiClient from '../api/client';

export const getExperiments = async () => {
  return apiClient<any[]>('/history/experiments?limit=50', { method: 'GET' });
};

export const getReportDetails = async (id: number) => {
  return apiClient<any>(`/history/reports/${id}`, { method: 'GET' });
};

export const searchRepository = async (query: string) => {
  return apiClient<any>('/history/search', {
    method: 'POST',
    body: JSON.stringify({ query, limit: 5 })
  });
};

export const extractInsights = async (topic: string) => {
  return apiClient<any>(`/history/insights?topic=${topic}`, { method: 'GET' });
};
