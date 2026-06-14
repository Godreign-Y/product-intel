import { request, getSystemSettings, delay } from '../utils/api-client';
import { mockRecommendations } from '../mocks/recommendations.mock';
export async function getRecommendations() {
    return request('/api/recommendations', mockRecommendations);
}
export async function applyRecommendation(id) {
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
            return await response.json();
        }
        catch (error) {
            throw new Error(`FastAPI apply recommendation failed. Details: ${error.message}`);
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
