import { request, getSystemSettings } from '../utils/api-client';
import { Recommendation } from '../types/recommendations';
import { mockRecommendations } from '../mocks/recommendations.mock';

/**
 * Retrieves the compiled list of business growth recommendations.
 * Queries `/optimization/maximize` for model-optimized parameters and merges them
 * with implementation status entries from the database.
 * 
 * @returns Promise resolving to recommendation items.
 */
export async function getRecommendations(): Promise<Recommendation[]> {
  const settings = getSystemSettings();

  if (settings.enableFastApi) {
    const baseUrl = settings.fastapiUrl.replace(/\/$/, '');
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${settings.apiKey}`,
    };

    // 1. Fetch optimal parameters from optimizer
    const optimizationPromise = fetch(`${baseUrl}/api/v1/optimization/maximize`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        product_id: 'P001',
        horizon_days: 30,
        target_metric: 'revenue',
        max_discount_pct: 30.0,
        max_marketing_budget: 20000.0
      })
    }).then(res => {
      if (!res.ok) throw new Error('Optimization query failed');
      return res.json();
    });

    // 2. Fetch implemented recommendation statuses
    const dbStatusPromise = fetch(`${baseUrl}/api/v1/db/recommendations`, {
      headers
    }).then(res => {
      if (!res.ok) return [];
      return res.json();
    });

    try {
      const [opts, dbRecs] = await Promise.all([
        optimizationPromise,
        dbStatusPromise
      ]);

      const totalLift = opts.optimized_forecast_sum - opts.baseline_forecast_sum;
      const optMarketing = opts.optimal_parameters?.marketing_spend || 12000;
      const baseMarketing = opts.baseline_parameters?.marketing_spend || 8500;

      // Update recommendations dynamically
      return mockRecommendations.map(rec => {
        // Match implementation status from database
        const dbEntry = dbRecs.find((r: any) => r.id === rec.id);
        const status = dbEntry ? dbEntry.status : 'Active';

        if (rec.id === 'rec_3') {
          // Meta ads optimization spend recommendations
          return {
            ...rec,
            description: `Increase marketing spend to optimal value of $${optMarketing.toLocaleString()} (baseline: $${baseMarketing.toLocaleString()}).`,
            businessValue: `+$${Math.round(totalLift * 0.4).toLocaleString()} annual revenue potential`,
            status
          };
        }

        if (rec.id === 'rec_2') {
          // Shipping optimizations
          const optDiscount = opts.optimal_parameters?.discount_pct || 15;
          return {
            ...rec,
            description: `Reduce shipping fees for orders near average cart values. Balance with optimal discount rate of ${optDiscount.toFixed(0)}%.`,
            businessValue: `+$${Math.round(totalLift * 0.35).toLocaleString()} annual revenue potential`,
            status
          };
        }

        // Default mapping logic
        let multiplier = 0.2;
        if (rec.id === 'rec_1') multiplier = 0.5;
        else if (rec.id === 'rec_4') multiplier = 0.25;
        else if (rec.id === 'rec_5') multiplier = 0.15;

        return {
          ...rec,
          businessValue: `+$${Math.round(totalLift * multiplier).toLocaleString()} annual revenue potential`,
          status
        };
      });

    } catch (error) {
      console.warn('Failed to compile recommendations from API. Falling back to mocks:', error);
      throw error;
    }
  }

  // Fallback to offline mock recommendations
  return request<Recommendation[]>('/api/recommendations', mockRecommendations);
}

/**
 * Marks a recommendation as implemented in the database.
 * 
 * @param id Recommendation unique ID.
 */
export async function applyRecommendation(id: string): Promise<Recommendation> {
  const settings = getSystemSettings();

  if (settings.enableFastApi) {
    const baseUrl = settings.fastapiUrl.replace(/\/$/, '');
    try {
      const response = await fetch(`${baseUrl}/api/v1/db/recommendations/${id}/apply`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${settings.apiKey}`,
        },
      });
      if (!response.ok) {
        throw new Error(`FastAPI apply recommendation failed: ${response.status}`);
      }
      
      const dbRec = await response.json();
      const matchedMock = mockRecommendations.find(r => r.id === id) || mockRecommendations[0];

      return {
        ...matchedMock,
        status: dbRec.status
      };
    } catch (error) {
      console.warn(`FastAPI apply recommendation failed. Details: ${(error as Error).message}`);
      throw error;
    }
  }

  // Fallback status change
  const found = mockRecommendations.find(r => r.id === id);
  if (!found) {
    throw new Error('Recommendation not found');
  }

  return {
    ...found,
    status: 'Implemented',
  };
}
