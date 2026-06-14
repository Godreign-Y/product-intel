'use client';

import React, { useState } from 'react';
import {
  Plus,
  Play,
  RotateCw,
  CheckCircle,
  FlaskConical,
  X,
} from 'lucide-react';
import { useExperiments } from '../../hooks/useExperiments';
import { ExperimentCard } from '../../components/ExperimentCard';
import { SimulationChart } from '../../components/Charts';
import { ExperimentVariable } from '../../types/experiments';

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

  const [activeTab, setActiveTab] = useState<'all' | 'create'>('all');

  // Form states
  const [name, setName] = useState('');
  const [objective, setObjective] = useState('');
  const [hypothesis, setHypothesis] = useState('');
  const [primaryMetric, setPrimaryMetric] = useState('Conversion Rate');
  const [type, setType] = useState<'A/B Test' | 'Multi-variant' | 'Simulation'>('Simulation');
  const [variables, setVariables] = useState<ExperimentVariable[]>([
    { id: '1', name: 'Shipping Cost', currentValue: '$5.00', newValue: '$4.50 (-10%)' },
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
    setVariables([{ id: '1', name: 'Shipping Cost', currentValue: '$5.00', newValue: '$4.50 (-10%)' }]);
    setActiveTab('all');
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Sub Tabs */}
      <div className="flex border-b border-slate-100 pb-px">
        <button
          onClick={() => setActiveTab('all')}
          className={`px-4 py-2.5 text-xs font-bold border-b-2 transition-all cursor-pointer ${
            activeTab === 'all'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-400 hover:text-slate-600'
          }`}
        >
          All Experiments
        </button>
        <button
          onClick={() => setActiveTab('create')}
          className={`px-4 py-2.5 text-xs font-bold border-b-2 transition-all cursor-pointer ${
            activeTab === 'create'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-400 hover:text-slate-600'
          }`}
        >
          Create Experiment
        </button>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-64 bg-white rounded-xl border border-slate-100 animate-pulse shadow-sm" />
          ))}
        </div>
      ) : activeTab === 'all' ? (
        /* Experiments Grid view */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {experiments.map((exp) => (
            <ExperimentCard key={exp.id} experiment={exp} />
          ))}
        </div>
      ) : (
        /* Create & Simulate Workspace layout */
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left: Form */}
          <div className="lg:col-span-2 bg-white rounded-xl border border-slate-100 shadow-sm p-6 space-y-5">
            <h3 className="text-base font-bold text-slate-900 pb-3 border-b border-slate-50">
              Create New Experiment
            </h3>

            <form onSubmit={handleSimulateClick} className="space-y-4">
              <div>
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-1">
                  Experiment Name
                </label>
                <input
                  type="text"
                  placeholder="e.g. Reduce shipping cost by 10%"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  className="w-full px-3.5 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-100"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-1">
                  Objective
                </label>
                <input
                  type="text"
                  placeholder="What do you want to achieve?"
                  value={objective}
                  onChange={(e) => setObjective(e.target.value)}
                  className="w-full px-3.5 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-100"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-1">
                  Hypothesis
                </label>
                <textarea
                  placeholder="Why do you believe this will have an impact?"
                  value={hypothesis}
                  onChange={(e) => setHypothesis(e.target.value)}
                  required
                  rows={3}
                  className="w-full px-3.5 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-100"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-1">
                    Primary Metric
                  </label>
                  <select
                    value={primaryMetric}
                    onChange={(e) => setPrimaryMetric(e.target.value)}
                    className="w-full px-3.5 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-indigo-500"
                  >
                    <option>Conversion Rate</option>
                    <option>Average Order Value</option>
                    <option>Add to Cart Rate</option>
                    <option>Revenue</option>
                    <option>Profit</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-1">
                    Type
                  </label>
                  <div className="flex gap-2.5 mt-1.5">
                    {['A/B Test', 'Multi-variant', 'Simulation'].map((t) => (
                      <label key={t} className="flex items-center gap-1.5 text-xs font-semibold cursor-pointer">
                        <input
                          type="radio"
                          name="expType"
                          checked={type === t}
                          onChange={() => setType(t as 'A/B Test' | 'Multi-variant' | 'Simulation')}
                          className="accent-indigo-600"
                        />
                        <span>{t}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>

              {/* Variables builder */}
              <div className="pt-4 border-t border-slate-50">
                <div className="flex justify-between items-center mb-3">
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-wider block">
                    Key Variables
                  </label>
                  <button
                    type="button"
                    onClick={addVariable}
                    className="text-xs text-indigo-600 hover:text-indigo-700 font-bold flex items-center gap-1 cursor-pointer"
                  >
                    <Plus className="w-3.5 h-3.5" /> Add Variable
                  </button>
                </div>

                <div className="space-y-3">
                  {variables.map((v, index) => (
                    <div key={v.id} className="flex flex-col md:flex-row gap-3 items-end bg-slate-50 p-3 rounded-lg border border-slate-100">
                      <div className="flex-1 min-w-0">
                        <span className="text-[10px] text-slate-400 font-semibold uppercase">Variable Name</span>
                        <input
                          type="text"
                          placeholder="e.g. Free shipping limit"
                          value={v.name}
                          onChange={(e) => handleVariableChange(v.id, 'name', e.target.value)}
                          required
                          className="w-full bg-white px-2.5 py-1.5 border border-slate-200 rounded text-xs focus:outline-none"
                        />
                      </div>
                      <div className="w-full md:w-32">
                        <span className="text-[10px] text-slate-400 font-semibold uppercase">Current Value</span>
                        <input
                          type="text"
                          placeholder="$50"
                          value={v.currentValue}
                          onChange={(e) => handleVariableChange(v.id, 'currentValue', e.target.value)}
                          required
                          className="w-full bg-white px-2.5 py-1.5 border border-slate-200 rounded text-xs focus:outline-none"
                        />
                      </div>
                      <div className="w-full md:w-32">
                        <span className="text-[10px] text-slate-400 font-semibold uppercase">New Value</span>
                        <input
                          type="text"
                          placeholder="$75"
                          value={v.newValue}
                          onChange={(e) => handleVariableChange(v.id, 'newValue', e.target.value)}
                          required
                          className="w-full bg-white px-2.5 py-1.5 border border-slate-200 rounded text-xs focus:outline-none"
                        />
                      </div>
                      {variables.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeVariable(v.id)}
                          className="p-2 text-rose-500 hover:bg-rose-50 rounded cursor-pointer"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              <div className="pt-4 flex justify-end gap-3 border-t border-slate-50">
                <button
                  type="submit"
                  disabled={isSimulating}
                  className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white rounded-xl text-xs font-bold transition-all shadow-sm flex items-center gap-1.5 cursor-pointer"
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

          {/* Right: Simulation Preview Pane */}
          <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-6 flex flex-col justify-between h-full min-h-[450px]">
            {isSimulating ? (
              <div className="h-full flex flex-col items-center justify-center text-center py-12">
                <div className="w-10 h-10 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mb-4" />
                <h4 className="text-sm font-bold text-slate-800">Processing Variables...</h4>
                <p className="text-xs text-slate-400 max-w-xs mt-1">
                  Machine learning model is running causal calculations and projecting cohort behavior.
                </p>
              </div>
            ) : !activePreview ? (
              <div className="h-full flex flex-col items-center justify-center text-center py-12 text-slate-400 px-4">
                <FlaskConical className="w-12 h-12 stroke-1 text-slate-300 mb-4" />
                <h4 className="text-sm font-bold text-slate-500">Simulation Preview</h4>
                <p className="text-xs text-slate-400 max-w-xs mt-1 leading-relaxed">
                  Enter your hypothesis and variables on the left, then click &quot;Run Simulation&quot; to forecast business metrics impact.
                </p>
              </div>
            ) : (
              <div className="space-y-6">
                <div className="flex justify-between items-center border-b border-slate-50 pb-3">
                  <h4 className="text-sm font-bold text-slate-800">Simulation Preview</h4>
                  <button onClick={clearPreview} className="text-slate-400 hover:text-slate-600 cursor-pointer">
                    <X className="w-4 h-4" />
                  </button>
                </div>

                {/* Expected Impact metrics row */}
                <div>
                  <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block mb-2">Expected Impact</span>
                  <div className="grid grid-cols-3 gap-2">
                    {activePreview.expectedImpact.map((imp) => (
                      <div key={imp.metric} className="bg-emerald-50/50 border border-emerald-100/50 p-2.5 rounded-lg text-center">
                        <span className="text-[9px] font-semibold text-slate-400 uppercase tracking-tight block">{imp.metric}</span>
                        <span className="text-sm font-bold text-emerald-600 mt-1 block">+{imp.percentChange}%</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Confidence Meter */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">Confidence Score</span>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-slate-100 h-2 rounded-full overflow-hidden">
                        <div className="bg-emerald-500 h-full" style={{ width: `${activePreview.confidenceScore}%` }} />
                      </div>
                      <span className="text-xs font-bold text-emerald-600">{activePreview.confidenceScore}%</span>
                    </div>
                  </div>
                  <div>
                    <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">Risk Level</span>
                    <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                      activePreview.riskLevel === 'High' ? 'bg-rose-50 text-rose-600 border border-rose-100' :
                      activePreview.riskLevel === 'Medium' ? 'bg-amber-50 text-amber-600 border border-amber-100' :
                      'bg-emerald-50 text-emerald-600 border border-emerald-100'
                    }`}>
                      {activePreview.riskLevel}
                    </span>
                  </div>
                </div>

                {/* Chart over time */}
                <div>
                  <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block mb-2">Revenue Impact Over Time</span>
                  <SimulationChart data={activePreview.revenueImpactOverTime} />
                </div>

                {/* Submit Launch button */}
                <div className="pt-4 border-t border-slate-50">
                  <button
                    onClick={handleLaunchClick}
                    className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold transition-all shadow-sm shadow-emerald-100 hover:shadow flex items-center justify-center gap-1.5 cursor-pointer"
                  >
                    <CheckCircle className="w-4 h-4" />
                    Launch Experiment
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
