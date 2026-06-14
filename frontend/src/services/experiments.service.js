import { request, getSystemSettings } from '../utils/api-client';
import { mockExperiments } from '../mocks/experiments.mock';
/**
 * Parses a frontend experiment variable into the change string format expected by the backend simulator.
 * E.g., name: "Shipping Cost", newValue: "$4.50 (-10%)" -> "shipping -10%"
 *
 * @param variable The variable structure from the UI form.
 * @returns Formatted change string (e.g. 'discount = 0.15').
 */
function parseVariableToChange(variable) {
    const nameLower = variable.name.toLowerCase();
    let backendName = 'discount';
    // Map user variable name to backend keyword
    if (nameLower.includes('marketing') || nameLower.includes('spend') || nameLower.includes('budget') || nameLower.includes('ad')) {
        backendName = 'marketing';
    }
    else if (nameLower.includes('shipping') || nameLower.includes('fee') || nameLower.includes('cost')) {
        backendName = 'shipping';
    }
    else if (nameLower.includes('price') || nameLower.includes('selling')) {
        backendName = 'price';
    }
    else if (nameLower.includes('inventory') || nameLower.includes('stock')) {
        backendName = 'inventory';
    }
    else if (nameLower.includes('traffic') || nameLower.includes('view')) {
        backendName = 'traffic';
    }
    const cleanVal = variable.newValue.trim().replace('$', '');
    // 1. Check for percentage relative changes, e.g., "(-10%)" or "+5%"
    const pctMatch = cleanVal.match(/([+-]?\d+(?:\.\d+)?)\s*%/);
    if (pctMatch) {
        const val = parseFloat(pctMatch[1]);
        return `${backendName} ${val >= 0 ? '+' : ''}${val}%`;
    }
    // 2. Check for absolute relative changes, e.g., "+150" or "-50"
    if (cleanVal.startsWith('+') || cleanVal.startsWith('-')) {
        const valMatch = cleanVal.match(/([+-]?\d+(?:\.\d+)?)/);
        if (valMatch) {
            return `${backendName} ${valMatch[1]}`;
        }
    }
    // 3. Fallback to direct absolute set, e.g., "4.50" or "0.15"
    const valMatch = cleanVal.match(/(\d+(?:\.\d+)?)/);
    if (valMatch) {
        return `${backendName} = ${valMatch[1]}`;
    }
    return `${backendName} = 0`;
}
/**
 * Retrieves all experiments from local db if FastAPI is enabled, otherwise mock data.
 */
export async function getExperiments() {
    const settings = getSystemSettings();
    if (settings.enableFastApi) {
        const baseUrl = settings.fastapiUrl.replace(/\/$/, '');
        return request('/api/v1/db/experiments', mockExperiments, { method: 'GET' });
    }
    return request('/api/experiments', mockExperiments);
}
/**
 * Runs a causal machine learning scenario simulation for the given variables.
 * Translates variables to change strings, queries /scenario/evaluate, and aggregates
 * the daily projection output into weekly chart increments.
 *
 * @returns SimulationPreview structure containing KPI differences and timelines.
 */
export async function simulateExperiment(name, objective, hypothesis, primaryMetric, type, variables) {
    const settings = getSystemSettings();
    if (settings.enableFastApi) {
        const baseUrl = settings.fastapiUrl.replace(/\/$/, '');
        const changes = variables.map(v => parseVariableToChange(v));
        try {
            const response = await fetch(`${baseUrl}/api/v1/scenario/evaluate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${settings.apiKey}`,
                },
                body: JSON.stringify({
                    product_id: 'P001',
                    horizon_days: 28, // 4 weeks exactly
                    changes
                }),
            });
            if (!response.ok) {
                throw new Error(`FastAPI scenario evaluate failed with status ${response.status}`);
            }
            const result = await response.json();
            const kpis = result.kpis || {};
            // Map expected impacts
            const expectedImpact = [
                {
                    metric: 'Conversion Rate',
                    percentChange: kpis.conversion_rate?.percentage_difference || 0,
                    isPositive: (kpis.conversion_rate?.percentage_difference || 0) >= 0
                },
                {
                    metric: 'Revenue',
                    percentChange: kpis.revenue?.percentage_difference || 0,
                    isPositive: (kpis.revenue?.percentage_difference || 0) >= 0
                },
                {
                    metric: 'Profit',
                    percentChange: kpis.profit?.percentage_difference || 0,
                    isPositive: (kpis.profit?.percentage_difference || 0) >= 0
                }
            ];
            // Sum daily values into weekly slices
            const revenuePoints = result.daily_comparison?.revenue || [];
            const weeklyPoints = [];
            for (let i = 0; i < 4; i++) {
                const slice = revenuePoints.slice(i * 7, (i + 1) * 7);
                let currentSum = 0;
                let simulatedSum = 0;
                for (const p of slice) {
                    currentSum += p.baseline_value;
                    simulatedSum += p.simulated_value;
                }
                weeklyPoints.push({
                    week: `Week ${i + 1}`,
                    current: Math.round(currentSum),
                    simulated: Math.round(simulatedSum)
                });
            }
            return {
                expectedImpact,
                confidenceScore: 86,
                riskLevel: Math.abs(kpis.revenue?.percentage_difference || 0) > 10 ? 'Medium' : 'Low',
                revenueImpactOverTime: weeklyPoints
            };
        }
        catch (error) {
            console.warn('Simulation API call failed. Details:', error);
            throw error;
        }
    }
    // Offline simulation preview calculation
    return new Promise((resolve) => {
        setTimeout(() => {
            const conversionChange = Math.random() * 5 + 1;
            const revenueChange = conversionChange * 0.7;
            const profitChange = revenueChange * 0.6;
            resolve({
                expectedImpact: [
                    { metric: 'Conversion Rate', percentChange: parseFloat(conversionChange.toFixed(1)), isPositive: true },
                    { metric: 'Revenue', percentChange: parseFloat(revenueChange.toFixed(1)), isPositive: true },
                    { metric: 'Profit', percentChange: parseFloat(profitChange.toFixed(1)), isPositive: true },
                ],
                confidenceScore: 85,
                riskLevel: 'Low',
                revenueImpactOverTime: [
                    { week: 'Week 1', current: 2100000, simulated: 2100000 * (1 + revenueChange / 400) },
                    { week: 'Week 2', current: 2150000, simulated: 2150000 * (1 + revenueChange / 250) },
                    { week: 'Week 3', current: 2200000, simulated: 2200000 * (1 + revenueChange / 150) },
                    { week: 'Week 4', current: 2300000, simulated: 2300000 * (1 + revenueChange / 100) },
                ],
            });
        }, 1200);
    });
}
export async function createExperiment(experiment) {
    const settings = getSystemSettings();
    if (settings.enableFastApi) {
        return request('/api/v1/db/experiments', { ...experiment, status: 'Running', createdAt: new Date().toISOString() }, {
            method: 'POST',
            body: JSON.stringify({
                ...experiment,
                status: 'Running',
            })
        });
    }
    return { ...experiment, status: 'Running', createdAt: new Date().toISOString() };
}
