import { useQuery } from '@tanstack/react-query';
import { getExperiments, getReportDetails, searchRepository, extractInsights } from '../services/experiments.service';

export const useExperiments = () => {
  return useQuery({
    queryKey: ['experiments'],
    queryFn: getExperiments,
    staleTime: 1 * 60 * 1000, // 1 minute cache
  });
};

export const useReportDetails = (id: number | null) => {
  return useQuery({
    queryKey: ['reportDetails', id],
    queryFn: () => getReportDetails(id as number),
    enabled: !!id,
    staleTime: 1 * 60 * 1000,
  });
};

export const useRepositorySearch = (query: string) => {
  return useQuery({
    queryKey: ['repositorySearch', query],
    queryFn: () => searchRepository(query),
    enabled: false, // triggered manually via refetch
    staleTime: 1 * 60 * 1000,
  });
};

export const useTopicInsights = (topic: string | null) => {
  return useQuery({
    queryKey: ['topicInsights', topic],
    queryFn: () => extractInsights(topic as string),
    enabled: !!topic,
    staleTime: 1 * 60 * 1000,
  });
};
