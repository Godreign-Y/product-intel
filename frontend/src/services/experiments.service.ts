import { request, getSystemSettings, delay } from '../utils/api-client';
import { Experiment, SimulationPreview, ExperimentVariable } from '../types/experiments';
import { mockExperiments, mockSimulationPreview } from '../mocks/experiments.mock';

export async function getExperiments(): Promise<Experiment[]> {
  return request<Experiment[]>('/api/experiments', mockExperiments);
}

export async function simulateExperiment(
  name: string,
  objective: string,
  hypothesis: string,
  primaryMetric: string,
  type: string,
  variables: ExperimentVariable[]
): Promise<SimulationPreview> {
  const settings = getSystemSettings();

  if (settings.enableFastApi) {
    const baseUrl = settings.fastapiUrl.replace(/\/$/, '');
    try {
      const response = await fetch(`${baseUrl}/api/experiments/simulate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${settings.apiKey}`,
        },
        body: JSON.stringify({ name, objective, hypothesis, primaryMetric, type, variables }),
      });
      if (!response.ok) {
        throw new Error(`FastAPI simulation failed: ${response.status}`);
      }
      return await response.json() as SimulationPreview;
    } catch (error) {
      throw new Error(`FastAPI simulation failed. Details: ${(error as Error).message}`);
    }
  }

  // Simulate server computation latency for the ML engine
  await delay(1500);

  // Generate some dynamic mock simulation previews based on values
  const conversionChange = Math.random() * 5 + 1; // 1% to 6%
  const revenueChange = conversionChange * 0.7;
  const profitChange = revenueChange * 0.6;
  const confidence = Math.floor(Math.random() * 20) + 75; // 75% to 95%

  return {
    expectedImpact: [
      { metric: 'Conversion Rate', percentChange: parseFloat(conversionChange.toFixed(1)), isPositive: true },
      { metric: 'Revenue', percentChange: parseFloat(revenueChange.toFixed(1)), isPositive: true },
      { metric: 'Profit', percentChange: parseFloat(profitChange.toFixed(1)), isPositive: true },
    ],
    confidenceScore: confidence,
    riskLevel: conversionChange > 4 ? 'Low' : 'Medium',
    revenueImpactOverTime: [
      { week: 'Week 1', current: 2100000, simulated: 2100000 * (1 + revenueChange / 400) },
      { week: 'Week 2', current: 2150000, simulated: 2150000 * (1 + revenueChange / 250) },
      { week: 'Week 3', current: 2200000, simulated: 2200000 * (1 + revenueChange / 150) },
      { week: 'Week 4', current: 2300000, simulated: 2300000 * (1 + revenueChange / 100) },
    ],
  };
}
