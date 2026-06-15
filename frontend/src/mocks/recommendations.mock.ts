/**
 * @deprecated This file is no longer used. Recommendations come from real API calls.
 * Kept for reference only.
 */

import { Recommendation } from '../types/recommendations';

export const mockRecommendations: Recommendation[] = [
  {
    id: 'rec_1',
    title: 'Reduce checkout steps from 5 to 3',
    description: 'Simplify checkout flow to remove friction.',
    category: 'Conversion',
    businessValue: '+$340K annual revenue potential',
    priority: 'High Impact',
    status: 'Active',
  },
  {
    id: 'rec_2',
    title: 'Lower shipping cost by 10%',
    description: 'Reduce shipping fees for orders near the average cart value.',
    category: 'Logistics',
    businessValue: '+$180K annual revenue potential',
    priority: 'High Impact',
    status: 'Active',
  },
  {
    id: 'rec_3',
    title: 'Increase ad spend on Meta (Retargeting)',
    description: 'Retarget past visitors with personalized ads.',
    category: 'Marketing',
    businessValue: '+$120K annual revenue potential',
    priority: 'Quick Win',
    status: 'Active',
  },
];
