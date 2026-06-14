import { request, getSystemSettings } from '../utils/api-client';
import { mockChatSessions, mockSuggestedQuestions } from '../mocks/ai-workspace.mock';
/**
 * Retrieves all chat sessions from the database.
 * If no session exists, automatically creates a default intelligence session.
 */
export async function getChatSessions() {
    const settings = getSystemSettings();
    if (settings.enableFastApi) {
        const baseUrl = settings.fastapiUrl.replace(/\/$/, '');
        try {
            const response = await fetch(`${baseUrl}/api/v1/db/chat/sessions`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${settings.apiKey}`,
                },
            });
            if (!response.ok) {
                throw new Error('Failed to retrieve chat sessions from DB');
            }
            const sessions = await response.json();
            if (sessions.length === 0) {
                // Automatically provision a default session thread
                const defaultSessionId = 'session_default';
                const defaultSessionPayload = {
                    id: defaultSessionId,
                    title: 'Executive Intelligence Workspace'
                };
                const createRes = await fetch(`${baseUrl}/api/v1/db/chat/sessions`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${settings.apiKey}`,
                    },
                    body: JSON.stringify(defaultSessionPayload),
                });
                if (createRes.ok) {
                    const created = await createRes.json();
                    return [created];
                }
            }
            return sessions;
        }
        catch (error) {
            console.warn('Chat sessions fetch from API failed. Error details:', error);
            throw error;
        }
    }
    return request('/api/chat/sessions', mockChatSessions);
}
/**
 * Deletes a chat session thread and its history.
 *
 * @param id Session unique ID.
 */
export async function deleteChatSession(id) {
    const settings = getSystemSettings();
    if (settings.enableFastApi) {
        const baseUrl = settings.fastapiUrl.replace(/\/$/, '');
        const response = await fetch(`${baseUrl}/api/v1/db/chat/sessions/${id}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${settings.apiKey}`,
            },
        });
        return response.ok;
    }
    return true;
}
/**
 * Retrieves the suggested question list.
 */
export async function getSuggestedQuestions() {
    return request('/api/chat/suggested-questions', mockSuggestedQuestions);
}
/**
 * Sends a chat message to the backend session message endpoint,
 * appending it to the history and retrieving the assistant's processed response.
 *
 * @param sessionId The targeted thread ID.
 * @param content The text content.
 * @param files Optional files.
 */
export async function sendChatMessage(sessionId, content, files) {
    const settings = getSystemSettings();
    if (settings.enableFastApi) {
        const baseUrl = settings.fastapiUrl.replace(/\/$/, '');
        // Inject file attachment metadata into the query string for the LLM
        let queryText = content;
        if (files && files.length > 0) {
            const fileNames = files.map(f => f.name).join(', ');
            queryText = `[File Attachments: ${fileNames}] ${content}`;
        }
        try {
            const response = await fetch(`${baseUrl}/api/v1/db/chat/sessions/${sessionId}/messages`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${settings.apiKey}`,
                },
                body: JSON.stringify({
                    content: queryText,
                    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                }),
            });
            if (!response.ok) {
                const errorDetail = await response.text();
                throw new Error(`FastAPI message save & agent query failed: ${errorDetail}`);
            }
            return await response.json();
        }
        catch (error) {
            console.warn('AI agent query execution failed. Details:', error);
            throw error;
        }
    }
    // Simulated fallback response (never hit when FastAPI is active)
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve({
                id: `msg_mock_${Date.now()}`,
                role: 'assistant',
                content: `I've analyzed your offline request: "${content}". Causal factors trace to seasonality adjustments.`,
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                suggestions: ['Show correlation details', 'Create experiment simulation', 'View recommendations']
            });
        }, 1200);
    });
}
