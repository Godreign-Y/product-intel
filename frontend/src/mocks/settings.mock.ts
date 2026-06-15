/**
 * @deprecated This file is no longer used. API configuration comes from environment variables.
 * Kept for reference only.
 */

import { SystemSettings } from '../types/settings';

export const mockSettings: SystemSettings = {
  dbStatus: 'Connected',
  notificationsEnabled: true,
  emailAlerts: true,
  selectedDataSources: ['Shopify Analytics', 'Google Analytics 4', 'Mixpanel'],
};
