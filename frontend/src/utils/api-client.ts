import { mockSettings } from '../mocks/settings.mock';
import { SystemSettings } from '../types/settings';

const SETTINGS_KEY = 'prodintel_settings';

export function getSystemSettings(): SystemSettings {
  if (typeof window === 'undefined') {
    return mockSettings;
  }
  const saved = localStorage.getItem(SETTINGS_KEY);
  if (!saved) {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(mockSettings));
    return mockSettings;
  }
  try {
    return JSON.parse(saved);
  } catch {
    return mockSettings;
  }
}

export function saveSystemSettings(settings: SystemSettings) {
  if (typeof window !== 'undefined') {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
  }
}

export const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export async function request<T>(endpoint: string, mockData: T): Promise<T> {
  const settings = getSystemSettings();
  await delay(settings.mockDelay || 800);

  if (settings.enableFastApi) {
    const baseUrl = settings.fastapiUrl.replace(/\/$/, '');
    try {
      const response = await fetch(`${baseUrl}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${settings.apiKey}`,
        },
      });
      if (!response.ok) {
        throw new Error(`FastAPI Request failed with status ${response.status}`);
      }
      return await response.json() as T;
    } catch (error) {
      console.warn(`FastAPI call to ${endpoint} failed, falling back to mock data. Error:`, error);
      // Fallback to mock data so pages never crash or stay blank when server is down
      return mockData;
    }
  }

  // Otherwise, return mock data
  return mockData;
}
