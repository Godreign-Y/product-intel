import { request, getSystemSettings, delay } from '../utils/api-client';
import { ChatSession, ChatMessage } from '../types/ai-workspace';
import { mockChatSessions, mockSuggestedQuestions, mockHypothesis } from '../mocks/ai-workspace.mock';

export async function getChatSessions(): Promise<ChatSession[]> {
  return request<ChatSession[]>('/api/chat/sessions', mockChatSessions);
}

export async function getSuggestedQuestions(): Promise<string[]> {
  return request<string[]>('/api/chat/suggested-questions', mockSuggestedQuestions);
}

export async function sendChatMessage(
  sessionId: string,
  content: string,
  files?: { name: string; size: string; type: string }[]
): Promise<ChatMessage> {
  const settings = getSystemSettings();
  
  if (settings.enableFastApi) {
    const baseUrl = settings.fastapiUrl.replace(/\/$/, '');
    try {
      const response = await fetch(`${baseUrl}/api/chat/sessions/${sessionId}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${settings.apiKey}`,
        },
        body: JSON.stringify({ content, files }),
      });
      if (!response.ok) {
        throw new Error(`FastAPI send message failed: ${response.status}`);
      }
      return await response.json() as ChatMessage;
    } catch (error) {
      throw new Error(`FastAPI send message failed. Details: ${(error as Error).message}`);
    }
  }

  // Simulate server latency
  await delay(1200);

  // Simple mock responses
  let replyText = `I've analyzed your question: "${content}". Based on current business trends, this could be related to changes in mobile traffic bounce rates (+4.2%) and AOV stabilization.`;
  let hypothesis;

  if (content.toLowerCase().includes('revenue') || content.toLowerCase().includes('sales')) {
    replyText = `Revenue trends show a 12.4% year-over-year increase, but mobile checkout conversion rate remains a bottleneck. Mobile visitors are converting 7.8% less than desktop visitors. I recommend simulating a checkout simplification experiment.`;
  } else if (content.toLowerCase().includes('anomaly') || content.toLowerCase().includes('anomalies')) {
    replyText = `I found 3 anomalies in the past 30 days:\n\n1. **Conversion rate dropped** (Severity: High) - June 18\n2. **Paid traffic spike** (Severity: Medium) - June 17\n3. **AOV fluctuation** (Severity: Low) - June 16\n\nWould you like me to generate a validation hypothesis for the conversion rate drop?`;
    hypothesis = mockHypothesis;
  } else if (content.toLowerCase().includes('checkout') || content.toLowerCase().includes('funnel')) {
    replyText = `Checkout funnel shows significant friction at step 2 (Shipping). The drop-off rate is 38% compared to the normal 24%. Let's look at simplifying the form fields from 5 steps to 3 steps.`;
    hypothesis = {
      ...mockHypothesis,
      title: 'Checkout step simplification reduces cart abandonment',
      description: 'Reducing checkout step complexity will keep users engaged and prevent session fatigue.',
    };
  }

  return {
    id: `msg_mock_${Date.now()}`,
    role: 'assistant',
    content: replyText,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    suggestions: [
      'Show correlation details',
      'Create experiment simulation',
      'View recommendations'
    ],
    hypothesis,
  };
}
