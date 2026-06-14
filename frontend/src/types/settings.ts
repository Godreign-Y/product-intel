export interface SystemSettings {
  fastapiUrl: string;
  enableFastApi: boolean;
  apiKey: string;
  dbStatus: 'Connected' | 'Disconnected' | 'Connecting';
  mockDelay: number;
  notificationsEnabled: boolean;
  emailAlerts: boolean;
  selectedDataSources: string[];
}
