export interface Recommendation {
  id: string;
  title: string;
  description: string;
  category: 'High Impact' | 'Quick Win' | 'Ongoing';
  expectedImpact: string;
  businessValue: string;
  confidenceLevel: number; // percentage
  priority: 'High' | 'Medium' | 'Low';
  status: 'Active' | 'Implemented' | 'Archived';
  tags: string[];
}
