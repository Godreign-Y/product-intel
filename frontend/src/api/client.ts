export const apiClient = async <T>(endpoint: string, options?: RequestInit): Promise<T> => {
  const baseUrl = '/api/v1'; // Assuming a proxy is set in vite.config.ts
  const url = endpoint.startsWith('http') ? endpoint : `${baseUrl}${endpoint}`;
  
  const headers = {
    'Content-Type': 'application/json',
    ...(options?.headers || {}),
  };

  const config: RequestInit = {
    ...options,
    headers,
  };

  const response = await fetch(url, config);
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    throw new Error(errorData?.detail || errorData?.message || `API Error: ${response.status} ${response.statusText}`);
  }
  
  return response.json();
};

export default apiClient;
