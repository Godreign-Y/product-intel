import { request } from '../utils/api-client';
import { mockPredictionsData } from '../mocks/predictions.mock';
export async function getPredictions(metric, timeframe) {
    // Translate UI metric selectors to mock keys
    const lookupKey = metric.toLowerCase().replace(/[^a-z]/g, '');
    const data = mockPredictionsData[lookupKey] || mockPredictionsData.revenue;
    // Custom endpoint formatting
    return request(`/api/predictions?metric=${metric}&timeframe=${timeframe}`, {
        ...data,
        metric,
        timeframe,
    });
}
