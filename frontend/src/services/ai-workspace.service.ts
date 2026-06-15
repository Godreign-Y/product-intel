/**
 * AI Workspace Service.
 *
 * Manages chat sessions, message history, and AI agent queries via the backend.
 * All data comes from real API calls — no mock fallbacks.
 *
 * @module ai-workspace.service
 */

import { getApiBaseUrl, getHeaders } from '../utils/api-client';
import { ChatSession, ChatMessage } from '../types/ai-workspace';

/**
 * Retrieves all chat sessions from the database.
 * If no session exists, automatically creates a default intelligence session.
 *
 * @returns Promise resolving to list of chat sessions.
 */
export async function getChatSessions(): Promise<ChatSession[]> {
  const baseUrl = getApiBaseUrl();
  const headers = getHeaders();

  const response = await fetch(`${baseUrl}/api/v1/db/chat/sessions`, {
    method: 'GET',
    headers: {
      Authorization: headers['Authorization'],
    },
  });

  if (!response.ok) {
    throw new Error('Failed to retrieve chat sessions from DB');
  }

  const sessions = (await response.json()) as ChatSession[];

  if (sessions.length === 0) {
    // Automatically provision a default session thread
    const defaultSessionPayload = {
      id: 'session_default',
      title: 'Executive Intelligence Workspace',
    };

    const createRes = await fetch(`${baseUrl}/api/v1/db/chat/sessions`, {
      method: 'POST',
      headers,
      body: JSON.stringify(defaultSessionPayload),
    });

    if (createRes.ok) {
      const created = (await createRes.json()) as ChatSession;
      return [created];
    }
  }

  return sessions;
}

/**
 * Deletes a chat session thread and its history.
 *
 * @param id - Session unique ID.
 * @returns Whether deletion was successful.
 */
export async function deleteChatSession(id: string): Promise<boolean> {
  const baseUrl = getApiBaseUrl();
  const headers = getHeaders();

  const response = await fetch(`${baseUrl}/api/v1/db/chat/sessions/${id}`, {
    method: 'DELETE',
    headers: {
      Authorization: headers['Authorization'],
    },
  });

  return response.ok;
}

/**
 * Sends a chat message to the backend session message endpoint,
 * appending it to the history and retrieving the assistant's processed response.
 *
 * @param sessionId - The targeted thread ID.
 * @param content - The text content.
 * @param files - Optional file attachments.
 * @returns The assistant's response message.
 */
export async function sendChatMessage(
  sessionId: string,
  content: string,
  files?: { name: string; size: string; type: string }[]
): Promise<ChatMessage> {
  const baseUrl = getApiBaseUrl();
  const headers = getHeaders();

  // Inject file attachment metadata into the query string for the LLM
  let queryText = content;
  if (files && files.length > 0) {
    const fileNames = files.map((f) => f.name).join(', ');
    queryText = `[File Attachments: ${fileNames}] ${content}`;
  }

  const response = await fetch(
    `${baseUrl}/api/v1/db/chat/sessions/${sessionId}/messages`,
    {
      method: 'POST',
      headers,
      body: JSON.stringify({
        content: queryText,
        timestamp: new Date().toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
        }),
      }),
    }
  );

  if (!response.ok) {
    const errorDetail = await response.text();
    throw new Error(`AI agent query failed: ${errorDetail}`);
  }

  return (await response.json()) as ChatMessage;
}
