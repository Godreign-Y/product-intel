export interface Evidence {
  text: string;
  impact?: string;
}

export interface Hypothesis {
  id: string;
  title: string;
  description: string;
  confidenceScore: number; // 0 - 100
  riskLevel: 'High' | 'Medium' | 'Low';
  supportingEvidence: Evidence[];
  contradictoryEvidence: Evidence[];
  suggestedValidation: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  suggestions?: string[];
  hypothesis?: Hypothesis;
  files?: { name: string; size: string; type: string }[];
}

export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: string;
}
