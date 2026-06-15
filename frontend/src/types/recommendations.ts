/**
 * Recommendation entity types.
 *
 * @module types/recommendations
 */

export interface Recommendation {
  id: string;
  title: string;
  description: string;
  /** Business category for the recommendation. */
  category: string;
  /** Projected business value from implementing this recommendation. */
  businessValue: string;
  /** Priority level based on impact assessment. */
  priority: 'High Impact' | 'Quick Win' | 'Ongoing';
  /** Implementation status. */
  status: 'Active' | 'Implemented' | 'Archived';
  /** Lucide icon name. */
  icon?: string;
  /** Estimated time to implement. */
  timeToImplement?: string;
  /** Effort level. */
  effort?: 'Low' | 'Medium' | 'High';
}
