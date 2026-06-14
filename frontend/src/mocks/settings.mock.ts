import { SystemSettings } from '../types/settings';

export const mockSettings: SystemSettings = {
  fastapiUrl: 'http://localhost:8000',
  enableFastApi: false,
  apiKey: 'pi_live_4f8e9a2b7c1d0e5f6g7h8i9j',
  dbStatus: 'Connected',
  mockDelay: 800,
  notificationsEnabled: true,
  emailAlerts: true,
  selectedDataSources: ['Shopify Analytics', 'Google Analytics 4', 'Mixpanel'],
};
