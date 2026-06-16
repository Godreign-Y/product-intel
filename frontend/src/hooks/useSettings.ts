import { useQuery } from '@tanstack/react-query';
import { getUserSettings } from '../services/settings.service';

export const useSettings = () => {
  return useQuery({
    queryKey: ['settings'],
    queryFn: getUserSettings,
    staleTime: Infinity, // Settings rarely change
  });
};
