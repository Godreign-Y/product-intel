import React, { useState } from 'react';
import {
  Plus,
  Play,
  RotateCw,
  CheckCircle,
  FlaskConical,
  X,
  TrendingUp,
  Percent,
  DollarSign,
} from 'lucide-react';
import { useExperiments } from '../hooks/useExperiments';
import { ExperimentCard } from '../components/ExperimentCard';
import { SimulationChart } from '../components/Charts';
import { ExperimentVariable } from '../types/experiments';

/**
 * Catalog of variables the backend scenario simulator supports.
 * Maps display names to backend variable keys with typical baseline values.
 */
const VARIABLE_CATALOG = [
  { label: 'Discount %', backendKey: 'discount', baseline: '15%' },
  { label: 'Marketing Spend', backendKey: 'marketing', baseline: '$8,500' },
  { label: 'Shipping Cost', backendKey: 'shipping', baseline: '$69' },
  { label: 'Selling Price', backendKey: 'price', baseline: '$720' },
  { label: 'Inventory', backendKey: 'inventory', baseline: '2,380' },
  { label: 'Traffic', backendKey: 'traffic', baseline: '3,800' },
];

export default function ExperimentsPage() {
  const {
    experiments,
    activePreview,
    isLoading,
    isSimulating,
    runSimulation,
    createExperiment,
    clearPreview,
  } = useExperiments();

  // Form states
  const [name, setName] = useState('');
  const [objective, setObjective] = useState('');
  const [hypothesis, setHypothesis] = useState('');
  const [primaryMetric, setPrimaryMetric] = useState('Conversion Rate');
  const [expectedOutcome, setExpectedOutcome] = useState('');
  const [type, setType] = useState<'A/B Test' | 'Multi-variant' | 'Simulation'>('Simulation');
  const [variables, setVariables] = useState<ExperimentVariable[]>([
    { id: '1', name: 'Discount %', currentValue: '15%', newValue: '+5%' },
  ]);

  const addVariable = () => {
    const newVar: ExperimentVariable = {
      id: Date.now().toString(),
      name: '',
      currentValue: '',
      newValue: '',
    };
    setVariables([...variables, newVar]);
  };

  const removeVariable = (id: string) => {
    setVariables(variables.filter((v) => v.id !== id));
  };

  const handleVariableChange = (id: string, field: keyof ExperimentVariable, val: string) => {
    setVariables(
      variables.map((v) => {
        if (v.id === id) {
          return { ...v, [field]: val };
        }
        return v;
      })
    );
  };

  const handleSimulateClick = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !hypothesis || variables.some((v) => !v.name)) return;
    runSimulation(name, objective, hypothesis, primaryMetric, type, variables);
  };

  const handleLaunchClick = () => {
    if (!name || !hypothesis) return;
    createExperiment({
      name,
      objective,
      hypothesis,
      primaryMetric,
      type,
      variables,
    });
    // Reset Form
    setName('');
    setObjective('');
    setHypothesis('');
    setExpectedOutcome('');
    setVariables([{ id: '1', name: 'Discount %', currentValue: '15%', newValue: '+5%' }]);
  };

  // Aggregated Stat Calculations — computed from real experiments
  const completedExps = experiments.filter((e) => e.status === 'Completed');
  const successRate = experiments.length > 0
    ? `${Math.round((completedExps.length / experiments.length) * 100)}%`
    : '—';
  const avgLift = completedExps.length > 0
    ? `+${(
        completedExps.reduce((sum, e) => {
          const impact = e.simulationPreview?.expectedImpact?.[0]?.percentChange || 0;
          return sum + impact;
        }, 0) / completedExps.length
      ).toFixed(1)}%`
    : '—';
  const totalRevImpact = completedExps.reduce((sum, e) => {
    const revImpact = e.simulationPreview?.expectedImpact?.find(
      (i: any) => i.metric === 'Revenue'
    )?.percentChange || 0;
    return sum + revImpact;
  }, 0);
  const revenueGenerated = totalRevImpact > 0
    ? `+$${Math.round(totalRevImpact * 10)}K`
    : '—';
  const stats = {
    total: experiments.length,
    successRate,
    avgLift,
    revenueGenerated,
  };

  return (
    <div className="space-y-8 pb-12">
      {/* Top Section: Experiment Statistics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white border border-[#E5E7EB] rounded-[20px] p-6 shadow-sm hover:shadow-md transition-all h-[120px] flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold text-[#6B7280]">Total Experiments</span>
            <p className="text-2xl font-extrabold text-[#111827] mt-1">{stats.total}</p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-purple-50 text-[#7C3AED] flex items-center justify-center">
            <FlaskConical className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white border border-[#E5E7EB] rounded-[20px] p-6 shadow-sm hover:shadow-md transition-all h-[120px] flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold text-[#6B7280]">Success Rate</span>
            <p className="text-2xl font-extrabold text-[#111827] mt-1">{stats.successRate}</p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-emerald-50 text-[#10B981] flex items-center justify-center">
            <Percent className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white border border-[#E5E7EB] rounded-[20px] p-6 shadow-sm hover:shadow-md transition-all h-[120px] flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold text-[#6B7280]">Average Lift</span>
            <p className="text-2xl font-extrabold text-[#111827] mt-1">{stats.avgLift}</p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-blue-50 text-[#3B82F6] flex items-center justify-center">
            <TrendingUp className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white border border-[#E5E7EB] rounded-[20px] p-6 shadow-sm hover:shadow-md transition-all h-[120px] flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold text-[#6B7280]">Revenue Generated</span>
            <p className="text-2xl font-extrabold text-[#111827] mt-1">{stats.revenueGenerated}</p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-amber-50 text-[#F59E0B] flex items-center justify-center">
            <DollarSign className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Main Section: Create & Simulate split layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Middle Section: Create Experiment Form Card (Left Column) */}
        <div className="lg:col-span-7 bg-white rounded-[20px] border border-[#E5E7EB] shadow-sm p-6 space-y-5">
          <h3 className="text-sm font-bold text-[#111827] pb-3 border-b border-slate-50 flex items-center gap-2">
            <FlaskConical className="w-4 h-4 text-[#7C3AED]" />
            Create Experiment
          </h3>

          <form onSubmit={handleSimulateClick} className="space-y-4">
            <div>
              <label className="text-[10px] font-bold text-[#6B7280] uppercase tracking-wider block mb-1">
                Experiment Name
              </label>
              <input
                type="text"
                placeholder="e.g. Reduce checkout steps from 5 to 3"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="w-full h-[44px] px-3.5 border border-[#E5E7EB] rounded-[12px] text-sm focus:outline-none focus:border-[#7C3AED] focus:ring-2 focus:ring-[#F3E8FF] transition-all"
              />
            </div>

            <div>
              <label className="text-[10px] font-bold text-[#6B7280] uppercase tracking-wider block mb-1">
                Hypothesis
              </label>
              <textarea
                placeholder="Simplify checkout flow to remove friction..."
                value={hypothesis}
                onChange={(e) => setHypothesis(e.target.value)}
                required
                rows={2}
                className="w-full p-3 border border-[#E5E7EB] rounded-[12px] text-sm focus:outline-none focus:border-[#7C3AED] focus:ring-2 focus:ring-[#F3E8FF] transition-all"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-[10px] font-bold text-[#6B7280] uppercase tracking-wider block mb-1">
                  Target Metric
                </label>
                <select
                  value={primaryMetric}
                  onChange={(e) => setPrimaryMetric(e.target.value)}
                  className="w-full h-[44px] px-3 border border-[#E5E7EB] rounded-[12px] text-sm focus:outline-none focus:border-[#7C3AED] bg-white"
                >
                  <option>Conversion Rate</option>
                  <option>Average Order Value</option>
                  <option>Revenue</option>
                  <option>Profit</option>
                </select>
              </div>

              <div>
                <label className="text-[10px] font-bold text-[#6B7280] uppercase tracking-wider block mb-1">
                  Expected Outcome
                </label>
                <input
                  type="text"
                  placeholder="e.g. +6.2% conversion lift"
                  value={expectedOutcome}
                  onChange={(e) => setExpectedOutcome(e.target.value)}
                  className="w-full h-[44px] px-3.5 border border-[#E5E7EB] rounded-[12px] text-sm focus:outline-none focus:border-[#7C3AED] focus:ring-2 focus:ring-[#F3E8FF] transition-all"
                />
              </div>
            </div>

            {/* Variables builder */}
            <div className="pt-3 border-t border-slate-50">
              <div className="flex justify-between items-center mb-3">
                <label className="text-[10px] font-bold text-[#6B7280] uppercase tracking-wider block">
                  Variables
                </label>
                <button
                  type="button"
                  onClick={addVariable}
                  className="text-xs text-[#7C3AED] hover:text-[#6D28D9] font-bold flex items-center gap-1 cursor-pointer"
                >
                  <Plus className="w-3.5 h-3.5" /> Add Variable
                </button>
              </div>

              <div className="space-y-3 max-h-48 overflow-y-auto pr-1">
                {variables.map((v) => (
                  <div key={v.id} className="flex flex-col md:flex-row gap-3 items-end bg-slate-50/50 p-3 rounded-[12px] border border-[#E5E7EB]">
                    <div className="flex-grow min-w-0">
                      <span className="text-[9px] text-[#9CA3AF] font-bold uppercase">Variable</span>
                      <select
                        value={v.name}
                        onChange={(e) => {
                          const selected = VARIABLE_CATALOG.find((c) => c.label === e.target.value);
                          handleVariableChange(v.id, 'name', e.target.value);
                          if (selected) {
                            handleVariableChange(v.id, 'currentValue', selected.baseline);
                          }
                        }}
                        required
                        className="w-full bg-white h-9 px-3 border border-[#E5E7EB] rounded-lg text-xs focus:outline-none focus:border-[#7C3AED] cursor-pointer"
                      >
                        <option value="">Select variable...</option>
                        {VARIABLE_CATALOG.map((c) => (
                          <option key={c.backendKey} value={c.label}>{c.label}</option>
                        ))}
                      </select>
                    </div>
                    <div className="w-full md:w-24">
                      <span className="text-[9px] text-[#9CA3AF] font-bold uppercase">Current</span>
                      <input
                        type="text"
                        placeholder="5"
                        value={v.currentValue}
                        onChange={(e) => handleVariableChange(v.id, 'currentValue', e.target.value)}
                        required
                        className="w-full bg-white h-9 px-3 border border-[#E5E7EB] rounded-lg text-xs focus:outline-none focus:border-[#7C3AED]"
                      />
                    </div>
                    <div className="w-full md:w-24">
                      <span className="text-[9px] text-[#9CA3AF] font-bold uppercase">New</span>
                      <input
                        type="text"
                        placeholder="3"
                        value={v.newValue}
                        onChange={(e) => handleVariableChange(v.id, 'newValue', e.target.value)}
                        required
                        className="w-full bg-white h-9 px-3 border border-[#E5E7EB] rounded-lg text-xs focus:outline-none focus:border-[#7C3AED]"
                      />
                    </div>
                    {variables.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeVariable(v.id)}
                        className="p-2 text-rose-500 hover:bg-rose-50 rounded-lg cursor-pointer"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div className="pt-3 flex justify-end gap-3 border-t border-slate-50">
              <button
                type="submit"
                disabled={isSimulating}
                className="h-[44px] px-5 bg-[#7C3AED] hover:bg-[#6D28D9] disabled:bg-purple-300 text-white rounded-[12px] text-xs font-bold transition-all shadow-sm flex items-center gap-1.5 cursor-pointer"
              >
                {isSimulating ? (
                  <>
                    <RotateCw className="w-4 h-4 animate-spin" />
                    Simulating...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    Run Simulation
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Results Section: Simulation Output (Right Column) */}
        <div className="lg:col-span-5 bg-white rounded-[20px] border border-[#E5E7EB] shadow-sm p-6 flex flex-col justify-between min-h-[480px]">
          {isSimulating ? (
            <div className="h-full flex flex-col items-center justify-center text-center py-12 flex-grow">
              <div className="w-10 h-10 border-4 border-[#7C3AED] border-t-transparent rounded-full animate-spin mb-4" />
              <h4 className="text-sm font-bold text-[#111827]">Processing Variables...</h4>
              <p className="text-xs text-[#6B7280] max-w-xs mt-1">
                Machine learning model is running causal calculations and projecting behavior.
              </p>
            </div>
          ) : !activePreview ? (
            <div className="h-full flex flex-col items-center justify-center text-center py-12 text-[#9CA3AF] px-4 flex-grow">
              <FlaskConical className="w-12 h-12 stroke-1 text-slate-300 mb-4" />
              <h4 className="text-sm font-bold text-[#6B7280]">Simulation Output</h4>
              <p className="text-xs text-[#9CA3AF] max-w-xs mt-1 leading-relaxed">
                Configure variables and run the simulation to view predicted outcomes and chart metrics.
              </p>
            </div>
          ) : (
            <div className="space-y-6 flex-grow flex flex-col justify-between">
              <div>
                <div className="flex justify-between items-center border-b border-slate-50 pb-3 mb-4">
                  <h4 className="text-sm font-bold text-[#111827]">Simulation Output</h4>
                  <button onClick={clearPreview} className="text-[#9CA3AF] hover:text-[#6B7280] cursor-pointer">
                    <X className="w-4 h-4" />
                  </button>
                </div>

                {/* Simulation Output Cards — from real simulation data */}
                <div className="space-y-3.5">
                  <span className="text-[10px] font-bold text-[#9CA3AF] uppercase tracking-wider block">Predicted Outcomes</span>
                  <div className="grid grid-cols-3 gap-3">
                    {activePreview.expectedImpact.map((impact, idx) => (
                      <div key={idx} className={`${impact.isPositive ? 'bg-emerald-50/50 border-emerald-100' : 'bg-rose-50/50 border-rose-100'} border p-2.5 rounded-xl text-center`}>
                        <span className="text-[9px] font-bold text-[#6B7280] uppercase tracking-tight block">{impact.metric}</span>
                        <span className={`text-xs font-extrabold mt-1 block ${impact.isPositive ? 'text-[#10B981]' : 'text-[#EF4444]'}`}>
                          {impact.isPositive ? '+' : ''}{impact.percentChange.toFixed(1)}% Impact
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 mt-4">
                  <div>
                    <span className="text-[10px] font-bold text-[#6B7280] uppercase tracking-wider block mb-1">Confidence</span>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-slate-100 h-1.5 rounded-full overflow-hidden">
                        <div className="bg-[#10B981] h-full" style={{ width: `${activePreview.confidenceScore}%` }} />
                      </div>
                      <span className="text-xs font-bold text-[#10B981]">{activePreview.confidenceScore}%</span>
                    </div>
                  </div>
                  <div>
                    <span className="text-[10px] font-bold text-[#6B7280] uppercase tracking-wider block mb-1">Risk Score</span>
                    <span className={`text-[10px] font-extrabold px-2 py-0.5 rounded uppercase ${
                      activePreview.riskLevel === 'High' ? 'bg-rose-50 text-[#EF4444]' :
                      activePreview.riskLevel === 'Medium' ? 'bg-amber-50 text-[#F59E0B]' :
                      'bg-emerald-50 text-[#10B981]'
                    }`}>
                      {activePreview.riskLevel} Risk
                    </span>
                  </div>
                </div>

                {/* Before vs After Visualization */}
                <div className="mt-4 pt-4 border-t border-slate-50">
                  <span className="text-[10px] font-bold text-[#6B7280] uppercase tracking-wider block mb-3">Before vs After Visualization</span>
                  <SimulationChart data={activePreview.revenueImpactOverTime} />
                </div>
              </div>

              {/* Submit Launch button */}
              <div className="pt-4 border-t border-slate-50 mt-6">
                <button
                  onClick={handleLaunchClick}
                  className="w-full h-[44px] bg-[#7C3AED] hover:bg-[#6D28D9] text-white rounded-[12px] text-xs font-bold transition-all shadow-sm hover:shadow flex items-center justify-center gap-1.5 cursor-pointer"
                >
                  <CheckCircle className="w-4 h-4" />
                  Launch Experiment
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* bottom list of experiments */}
      <div>
        <h3 className="text-sm font-bold text-[#111827] mb-4">All Active Experiments</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {experiments.map((exp) => (
            <ExperimentCard key={exp.id} experiment={exp} />
          ))}
        </div>
      </div>
    </div>
  );
}
