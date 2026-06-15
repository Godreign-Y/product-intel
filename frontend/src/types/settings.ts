/**
 * System-level settings for the Product Intelligence frontend.
 *
 * API connection config (URL, key) is managed via environment variables,
 * not stored in these settings. These settings cover user preferences only.
 */
export interface SystemSettings {
  /** Current backend connection health status. */
  dbStatus: 'Connected' | 'Disconnected' | 'Connecting';
  /** Whether in-app notifications are enabled. */
  notificationsEnabled: boolean;
  /** Whether email alert digests are enabled. */
  emailAlerts: boolean;
  /** List of connected data source labels. */
  selectedDataSources: string[];
}
