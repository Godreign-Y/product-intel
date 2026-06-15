/**
 * API Client for Product Intelligence Frontend.
 *
 * Reads configuration from environment variables (VITE_API_BASE_URL, VITE_API_KEY).
 * All requests go directly to the FastAPI backend — no mock data, no fallbacks.
 *
 * @module api-client
 */

/** Base URL for the FastAPI backend, sourced from environment. */
const API_BASE_URL: string = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');

/** API authentication key, sourced from environment. */
const API_KEY: string = import.meta.env.VITE_API_KEY || '';

/**
 * Returns the configured API base URL.
 */
export function getApiBaseUrl(): string {
  return API_BASE_URL;
}

/**
 * Returns the configured API key.
 */
export function getApiKey(): string {
  return API_KEY;
}

/**
 * Builds the standard request headers for all API calls.
 *
 * @returns Headers object with Content-Type and Authorization.
 */
export function getHeaders(): Record<string, string> {
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${API_KEY}`,
  };
}

/**
 * Performs a typed HTTP request to the FastAPI backend.
 *
 * @template T - Expected response type.
 * @param endpoint - API path (e.g., '/api/v1/analytics/kpi').
 * @param options - Optional fetch RequestInit overrides.
 * @returns Promise resolving to the parsed JSON response.
 * @throws Error if the request fails or returns non-OK status.
 */
export async function request<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const fetchOptions: RequestInit = {
    method: options?.method || 'GET',
    headers: {
      ...getHeaders(),
      ...(options?.headers || {}),
    },
  };

  if (options?.body) {
    fetchOptions.body = options.body;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, fetchOptions);

  if (!response.ok) {
    const errorBody = await response.text().catch(() => '');
    throw new Error(
      `API request to ${endpoint} failed (${response.status}): ${errorBody || response.statusText}`
    );
  }

  return (await response.json()) as T;
}
