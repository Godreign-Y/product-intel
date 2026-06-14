import { ChatSession, Hypothesis } from '../types/ai-workspace';

export const mockHypothesis: Hypothesis = {
  id: 'hyp_workspace_1',
  title: 'Mobile checkout page latency is causing conversion drops',
  description: 'Recent release on mobile checkout introduced a JS bundle size increase, causing higher page load times on 3G/4G networks, leading to cart abandonment.',
  confidenceScore: 84,
  riskLevel: 'Medium',
  supportingEvidence: [
    { text: 'Mobile checkout load time increased by 1.8 seconds (+45%)', impact: 'High Impact' },
    { text: 'Conversion rate decreased by 7.8% on mobile devices', impact: 'High Impact' },
    { text: 'Session abandonment at checkout increased by 15%', impact: 'Medium Impact' }
  ],
  contradictoryEvidence: [
    { text: 'Desktop conversion rate remained flat (+0.2%)', impact: 'Confirms mobile-only nature' },
    { text: 'Server response time (TTFB) remained unchanged at 85ms', impact: 'Indicates client-side issue' }
  ],
  suggestedValidation: 'Run a performance audit on client-side bundles and set up a synthetic performance test monitoring mobile loading speed.'
};

export const mockChatSessions: ChatSession[] = [
  {
    id: 'session_1',
    title: 'Revenue Drop Analysis',
    createdAt: '2026-06-18T10:00:00Z',
    messages: [
      {
        id: 'msg_1',
        role: 'user',
        content: 'Why did revenue drop last week?',
        timestamp: '10:00 AM'
      },
      {
        id: 'msg_2',
        role: 'assistant',
        content: 'Revenue dropped by 6% compared to the previous week. Here are the top contributing factors:\n\n1. **Paid traffic decreased by 15%** (Impact: -$128K)\n2. **Mobile conversion rate decreased by 6%** (Impact: -$66K)\n3. **Returning users decreased by 9%** (Impact: -$45K)\n\nWould you like to dive deeper into any of these factors?',
        timestamp: '10:01 AM',
        suggestions: [
          'Analyze mobile conversion decline',
          'Investigate paid traffic decrease',
          'Review returning user demographics'
        ],
        hypothesis: mockHypothesis
      }
    ]
  },
  {
    id: 'session_2',
    title: 'Checkout Funnel Audit',
    createdAt: '2026-06-17T15:30:00Z',
    messages: [
      {
        id: 'msg_3',
        role: 'user',
        content: 'Analyze our checkout funnel performance.',
        timestamp: '3:30 PM'
      },
      {
        id: 'msg_4',
        role: 'assistant',
        content: 'I analyzed the checkout funnel for June 10 - June 17, 2026. The biggest drop-off occurs at the **Shipping Information** step, where abandonment rate rose from 24% to 38%.\n\n* **Cart page to Shipping**: 85% transition (Normal)\n* **Shipping to Payment**: 54% transition (-14% vs last month)\n* **Payment to Confirmation**: 92% transition (Normal)\n\nThis drop-off coincides with the recent change in our free-shipping banner positioning.',
        timestamp: '3:31 PM',
        suggestions: [
          'Show shipping step details',
          'Run a checkout experiment simulation',
          'Check shipping costs impact'
        ]
      }
    ]
  }
];

export const mockSuggestedQuestions = [
  'What are the top growth opportunities?',
  'Show anomalies in the last 30 days',
  'Which campaign had the highest ROI?',
  'Segment users by lifetime value',
  'Analyze checkout funnel',
  'Forecast revenue for next month'
];
