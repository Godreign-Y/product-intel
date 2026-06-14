export interface ExperimentVariable {
  id: string;
  name: string;
  currentValue: string;
  newValue: string;
}

export interface SimulationMetricImpact {
  metric: string;
  percentChange: number;
  isPositive: boolean;
}

export interface SimulationResultPoint {
  week: string;
  current: number;
  simulated: number;
}

export interface SimulationPreview {
  expectedImpact: SimulationMetricImpact[];
  confidenceScore: number;
  riskLevel: 'High' | 'Medium' | 'Low';
  revenueImpactOverTime: SimulationResultPoint[];
}

export interface Experiment {
  id: string;
  name: string;
  objective: string;
  hypothesis: string;
  primaryMetric: string;
  type: 'A/B Test' | 'Multi-variant' | 'Simulation';
  status: 'Running' | 'Completed' | 'Draft';
  createdAt: string;
  variables: ExperimentVariable[];
  simulationPreview?: SimulationPreview;
  result?: string;
  changePercent?: number;
  isPositive?: boolean;
}
