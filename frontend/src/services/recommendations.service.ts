import { request, getSystemSettings, delay } from '../utils/api-client';
import { Recommendation } from '../types/recommendations';
import { mockRecommendations } from '../mocks/recommendations.mock';

export async function getRecommendations(): Promise<Recommendation[]> {
  return request<Recommendation[]>('/api/recommendations', mockRecommendations);
}

export async function applyRecommendation(id: string): Promise<Recommendation> {
  const settings = getSystemSettings();

  if (settings.enableFastApi) {
    const baseUrl = settings.fastapiUrl.replace(/\/$/, '');
    try {
      const response = await fetch(`${baseUrl}/api/recommendations/${id}/apply`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${settings.apiKey}`,
        },
      });
      if (!response.ok) {
        throw new Error(`FastAPI apply recommendation failed: ${response.status}`);
      }
      return await response.json() as Recommendation;
    } catch (error) {
      throw new Error(`FastAPI apply recommendation failed. Details: ${(error as Error).message}`);
    }
  }

  await delay(800);
  const found = mockRecommendations.find(r => r.id === id);
  if (!found) {
    throw new Error('Recommendation not found');
  }
  
  // Return updated recommendation status
  return {
    ...found,
    status: 'Implemented',
  };
}
