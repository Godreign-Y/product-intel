import { getSystemSettings, saveSystemSettings, delay } from '../utils/api-client';
export async function getSettings() {
    await delay(300);
    return getSystemSettings();
}
export async function updateSettings(settings) {
    await delay(500);
    saveSystemSettings(settings);
    return settings;
}
export async function testFastApiConnection(url, apiKey) {
    await delay(1000);
    const baseUrl = url.replace(/\/$/, '');
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);
        const response = await fetch(`${baseUrl}/health`, {
            signal: controller.signal,
            headers: {
                'Authorization': `Bearer ${apiKey}`,
            },
        });
        clearTimeout(timeoutId);
        if (response.ok) {
            return 'Connected';
        }
        return 'Disconnected';
    }
    catch (error) {
        console.warn('FastAPI health check failed:', error);
        return 'Disconnected';
    }
}
