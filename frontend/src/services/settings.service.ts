/**
 * Settings Service.
 *
 * Manages frontend user preferences stored in localStorage.
 * API connection config (URL, key) comes from environment variables.
 *
 * @module settings.service
 */

import { getApiBaseUrl, getApiKey } from '../utils/api-client';
import { SystemSettings } from '../types/settings';

const SETTINGS_KEY = 'prodintel_settings';

/** Default settings values for first-time users. */
const DEFAULT_SETTINGS: SystemSettings = {
  dbStatus: 'Connecting',
  notificationsEnabled: true,
  emailAlerts: true,
  selectedDataSources: ['Shopify Analytics', 'Google Analytics 4', 'Mixpanel'],
};

/**
 * Retrieves system settings from localStorage.
 *
 * @returns Current system settings.
 */
export async function getSettings(): Promise<SystemSettings> {
  if (typeof window === 'undefined') {
    return DEFAULT_SETTINGS;
  }

  const saved = localStorage.getItem(SETTINGS_KEY);
  if (!saved) {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(DEFAULT_SETTINGS));
    return DEFAULT_SETTINGS;
  }

  try {
    return JSON.parse(saved);
  } catch {
    return DEFAULT_SETTINGS;
  }
}

/**
 * Persists updated settings to localStorage.
 *
 * @param settings - The updated settings to save.
 * @returns The saved settings.
 */
export async function updateSettings(
  settings: SystemSettings
): Promise<SystemSettings> {
  if (typeof window !== 'undefined') {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
  }
  return settings;
}

/**
 * Tests the FastAPI backend health endpoint using the env-configured URL.
 *
 * @returns Connection status string.
 */
export async function testFastApiConnection(): Promise<'Connected' | 'Disconnected'> {
  const baseUrl = getApiBaseUrl();
  const apiKey = getApiKey();

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    const response = await fetch(`${baseUrl}/health`, {
      signal: controller.signal,
      headers: {
        Authorization: `Bearer ${apiKey}`,
      },
    });

    clearTimeout(timeoutId);
    return response.ok ? 'Connected' : 'Disconnected';
  } catch (error) {
    console.warn('FastAPI health check failed:', error);
    return 'Disconnected';
  }
}
