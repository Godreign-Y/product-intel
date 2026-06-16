import React, { useState } from 'react';
import { Line } from 'react-chartjs-2';
import 'chart.js/auto';
import { ArrowUpRight, ArrowDownRight, RefreshCw } from 'lucide-react';
import { useFilters } from '../components/FilterContext';
import { GlobalFilterBar } from '../components/GlobalFilterBar';
import { usePredictions } from '../hooks/usePredictions';
import { LoadingState, ErrorState } from '../components/LoadingErrorState';

export default function PredictionsPage() {
  const { selectedProduct, selectedCategory, startDate, endDate } = useFilters();
  
  const [trendMetric, setTrendMetric] = useState('revenue');
  const [trendGranularity, setTrendGranularity] = useState('daily');

  const { data, isLoading, isError, error, refetch, isFetching } = usePredictions({
    product_id: selectedProduct || null,
    category: selectedCategory || null,
    start_date: startDate || null,
    end_date: endDate || null,
    metric: trendMetric,
    granularity: trendGranularity
  });

  const trendData = data?.data;

  const trendChartConfig = trendData?.history ? {
    labels: trendData.history.map(pt => pt.date),
    datasets: [{
      label: trendMetric.toUpperCase(),
      data: trendData.history.map(pt => pt.value),
      borderColor: '#8b5cf6',
      backgroundColor: 'rgba(139, 92, 246, 0.1)',
      borderWidth: 2,
      tension: 0.4,
      fill: true,
      pointRadius: trendData.history.length > 30 ? 0 : 3,
      pointHoverRadius: 5
    }]
  } : null;

  return (
    <>
      <div className="header">
        <div>
          <h1>Historical Trends</h1>
          <p>Longitudinal tracking and regression analysis</p>
        </div>
        <button 
          onClick={() => refetch()}
          className="filter-select"
          style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}
          disabled={isFetching}
        >
          <RefreshCw size={14} className={isFetching ? 'spin' : ''} />
          Sync
        </button>
      </div>

      <GlobalFilterBar />

      <div className="animate-fade-in">
        {isLoading ? (
          <LoadingState message="Analyzing Linear Time-Series Models..." />
        ) : isError ? (
          <ErrorState message={error instanceof Error ? error.message : 'Unknown error'} onRetry={() => refetch()} />
        ) : (
          <div className="chart-card" style={{ marginBottom: '28px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ margin: 0 }}>Metric Trajectory ({trendMetric.replace('_', ' ').toUpperCase()})</h3>
              
              <div style={{ display: 'flex', gap: '12px' }}>
                <div className="filter-group" style={{ margin: 0, minWidth: '150px' }}>
                  <select 
                    className="filter-select"
                    value={trendMetric}
                    onChange={(e) => setTrendMetric(e.target.value)}
                  >
                    <option value="revenue">Revenue</option>
                    <option value="orders">Orders</option>
                    <option value="conversion_rate">Conversion Rate</option>
                    <option value="retention_rate">Retention Rate</option>
                  </select>
                </div>
                <div style={{ display: 'flex', background: 'rgba(0,0,0,0.2)', padding: '4px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                  {['daily', 'weekly', 'monthly', 'quarterly'].map(gran => (
                    <button 
                      key={gran}
                      className={`granularity-btn ${trendGranularity === gran ? 'active' : ''}`}
                      onClick={() => setTrendGranularity(gran)}
                    >
                      {gran.charAt(0).toUpperCase() + gran.slice(1)}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div style={{ height: '360px', position: 'relative' }}>
              {trendChartConfig ? (
                <Line 
                  data={trendChartConfig}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                      y: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                      x: { ticks: { color: '#9ca3af' }, grid: { display: false } }
                    }
                  }}
                />
              ) : <p style={{ textAlign: 'center', padding: '40px' }}>No Trend Data Available.</p>}
            </div>

            {trendData && (
              <div className="trend-stats animate-fade-in">
                <div className="trend-stat-card">
                  <label>Regression Direction</label>
                  <p style={{ 
                    color: trendData.direction === 'increasing' ? 'var(--success)' : 
                           trendData.direction === 'decreasing' ? 'var(--danger)' : 'var(--text-primary)',
                    display: 'flex', alignItems: 'center', gap: '6px'
                  }}>
                    {trendData.direction === 'increasing' && <ArrowUpRight size={18} />}
                    {trendData.direction === 'decreasing' && <ArrowDownRight size={18} />}
                    {trendData.direction?.toUpperCase()}
                  </p>
                </div>
                <div className="trend-stat-card">
                  <label>Period Growth Rate</label>
                  <p style={{ 
                    color: (trendData.growth_rate_pct || 0) > 0 ? 'var(--success)' : 
                           (trendData.growth_rate_pct || 0) < 0 ? 'var(--danger)' : 'var(--text-primary)'
                  }}>
                    {(trendData.growth_rate_pct || 0) > 0 ? '+' : ''}{trendData.growth_rate_pct}%
                  </p>
                </div>
                <div className="trend-stat-card">
                  <label>R-Squared Fit</label>
                  <p>{((trendData.r_squared || 0) * 100).toFixed(2)}%</p>
                </div>
                <div className="trend-stat-card">
                  <label>Trend Confidence (P-value)</label>
                  <p>{(trendData.p_value || 1) < 0.05 ? 'Significant (< 5%)' : 'Weak/No effect'}</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
}
