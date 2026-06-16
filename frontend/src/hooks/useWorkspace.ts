import { useMutation } from '@tanstack/react-query';
import { sendWorkspaceQuery, ChatPayload } from '../services/workspace.service';

export const useWorkspace = () => {
  return useMutation({
    mutationFn: (payload: ChatPayload) => sendWorkspaceQuery(payload),
  });
};
