import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getChatSessions, getSuggestedQuestions, sendChatMessage } from '../services/ai-workspace.service';
export function useAIWorkspace() {
    const queryClient = useQueryClient();
    const [activeSessionId, setActiveSessionId] = useState(null);
    const [localSessions, setLocalSessions] = useState([]);
    // Fetch initial sessions
    const { data: sessions, isLoading, isError, error } = useQuery({
        queryKey: ['chatSessions'],
        queryFn: getChatSessions,
        refetchOnWindowFocus: false,
    });
    const { data: suggestedQuestions } = useQuery({
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
        mutationFn: async ({ sessionId, content, files, }) => {
            return sendChatMessage(sessionId, content, files);
        },
        onMutate: async (variables) => {
            // Create user message and append it locally immediately (Optimistic update)
            const userMessage = {
                id: `msg_user_${Date.now()}`,
                role: 'user',
                content: variables.content,
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                files: variables.files,
            };
            setLocalSessions((prev) => prev.map((s) => {
                if (s.id === variables.sessionId) {
                    return {
                        ...s,
                        messages: [...s.messages, userMessage],
                    };
                }
                return s;
            }));
        },
        onSuccess: (botReply, variables) => {
            // Append bot reply to the active session
            setLocalSessions((prev) => prev.map((s) => {
                if (s.id === variables.sessionId) {
                    return {
                        ...s,
                        messages: [...s.messages, botReply],
                    };
                }
                return s;
            }));
        },
        onError: (err, variables) => {
            // Append an error message from assistant
            const errorMessage = {
                id: `msg_err_${Date.now()}`,
                role: 'assistant',
                content: `Error: Failed to get response. ${err.message}`,
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            };
            setLocalSessions((prev) => prev.map((s) => {
                if (s.id === variables.sessionId) {
                    return {
                        ...s,
                        messages: [...s.messages, errorMessage],
                    };
                }
                return s;
            }));
        },
    });
    const sendMessage = (content, files) => {
        if (!activeSessionId)
            return;
        sendMessageMutation.mutate({ sessionId: activeSessionId, content, files });
    };
    const createNewSession = () => {
        const newSession = {
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
