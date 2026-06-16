import apiClient from '../api/client';
import { ChatResponse } from '../types';

export interface ChatPayload {
  query: string;
  context: {
    product_id: string | null;
    start_date: string | null;
    end_date: string | null;
  };
}

export const sendWorkspaceQuery = async (payload: ChatPayload): Promise<ChatResponse> => {
  return apiClient<ChatResponse>('/agent/query', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
};
