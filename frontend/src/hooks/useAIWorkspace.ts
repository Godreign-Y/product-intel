import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getChatSessions, getSuggestedQuestions, sendChatMessage } from '../services/ai-workspace.service';
import { ChatSession, ChatMessage } from '../types/ai-workspace';

export function useAIWorkspace() {
  const queryClient = useQueryClient();
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [localSessions, setLocalSessions] = useState<ChatSession[]>([]);

  // Fetch initial sessions
  const { data: sessions, isLoading, isError, error } = useQuery<ChatSession[], Error>({
    queryKey: ['chatSessions'],
    queryFn: getChatSessions,
    refetchOnWindowFocus: false,
  });

  const { data: suggestedQuestions } = useQuery<string[], Error>({
    queryKey: ['suggestedQuestions'],
    queryFn: getSuggestedQuestions,
    refetchOnWindowFocus: false,
  });

  // Sync react-query fetched sessions to local state
  useEffect(() => {
    if (sessions) {
      setLocalSessions(sessions);
      if (sessions.length > 0 && !activeSessionId) {
        setActiveSessionId(sessions[0].id);
      }
    }
  }, [sessions]);

  const activeSession = localSessions.find((s) => s.id === activeSessionId) || null;

  // Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: async ({
      sessionId,
      content,
      files,
    }: {
      sessionId: string;
      content: string;
      files?: { name: string; size: string; type: string }[];
    }) => {
      return sendChatMessage(sessionId, content, files);
    },
    onMutate: async (variables) => {
      // Create user message and append it locally immediately (Optimistic update)
      const userMessage: ChatMessage = {
        id: `msg_user_${Date.now()}`,
        role: 'user',
        content: variables.content,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        files: variables.files,
      };

      setLocalSessions((prev) =>
        prev.map((s) => {
          if (s.id === variables.sessionId) {
            return {
              ...s,
              messages: [...s.messages, userMessage],
            };
          }
          return s;
        })
      );
    },
    onSuccess: (botReply, variables) => {
      // Append bot reply to the active session
      setLocalSessions((prev) =>
        prev.map((s) => {
          if (s.id === variables.sessionId) {
            return {
              ...s,
              messages: [...s.messages, botReply],
            };
          }
          return s;
        })
      );
    },
    onError: (err, variables) => {
      // Append an error message from assistant
      const errorMessage: ChatMessage = {
        id: `msg_err_${Date.now()}`,
        role: 'assistant',
        content: `Error: Failed to get response. ${err.message}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setLocalSessions((prev) =>
        prev.map((s) => {
          if (s.id === variables.sessionId) {
            return {
              ...s,
              messages: [...s.messages, errorMessage],
            };
          }
          return s;
        })
      );
    },
  });

  const sendMessage = (content: string, files?: { name: string; size: string; type: string }[]) => {
    if (!activeSessionId) return;
    sendMessageMutation.mutate({ sessionId: activeSessionId, content, files });
  };

  const createNewSession = () => {
    const newSession: ChatSession = {
      id: `session_${Date.now()}`,
      title: `New Session ${localSessions.length + 1}`,
      messages: [],
      createdAt: new Date().toISOString(),
    };
    setLocalSessions((prev) => [newSession, ...prev]);
    setActiveSessionId(newSession.id);
  };

  return {
    sessions: localSessions,
    activeSession,
    activeSessionId,
    setActiveSessionId,
    suggestedQuestions: suggestedQuestions || [],
    isLoading,
    isError,
    error,
    isSending: sendMessageMutation.isPending,
    sendMessage,
    createNewSession,
  };
}
