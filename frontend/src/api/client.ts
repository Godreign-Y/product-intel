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
    let detail = errorData?.message || `API Error: ${response.status} ${response.statusText}`;
    if (errorData?.detail) {
      detail = Array.isArray(errorData.detail)
        ? errorData.detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join('; ')
        : String(errorData.detail);
    }
    throw new Error(detail);
  }
  
  return response.json();
};

export default apiClient;
