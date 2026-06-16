import React from 'react';
import { Bar, Doughnut } from 'react-chartjs-2';
import 'chart.js/auto';
import { Package, Users, RefreshCw } from 'lucide-react';
import { useFilters } from '../components/FilterContext';
import { GlobalFilterBar } from '../components/GlobalFilterBar';
import { DashboardKpiCards } from '../components/DashboardKpiCards';
import { formatNumber } from '../utils/formatters';
import { useDashboard } from '../hooks/useDashboard';
import { LoadingState, ErrorState } from '../components/LoadingErrorState';

export default function DashboardPage() {
  const { selectedProduct, selectedCategory, startDate, endDate } = useFilters();
  
  const { data, isLoading, isError, error, refetch, isFetching } = useDashboard({
    product_id: selectedProduct || null,
    category: selectedCategory || null,
    start_date: startDate || null,
    end_date: endDate || null
  });

  const channelChartConfig = data?.channelData?.channel_mix ? {
    labels: Object.keys(data.channelData.channel_mix),
    datasets: [{
      data: Object.values(data.channelData.channel_mix).map((v: any) => v * 100),
      backgroundColor: ['#8b5cf6', '#10b981', '#06b6d4', '#f59e0b'],
      borderWidth: 0,
      hoverOffset: 4
    }]
  } : null;

  const campaignChartConfig = data?.campaignData?.campaign_mix ? {
    labels: Object.keys(data.campaignData.campaign_mix),
    datasets: [{
      label: 'Campaign Mix Share (%)',
      data: Object.values(data.campaignData.campaign_mix).map((v: any) => v * 100),
      backgroundColor: ['rgba(139, 92, 246, 0.6)', 'rgba(16, 185, 129, 0.6)', 'rgba(6, 182, 212, 0.6)', 'rgba(245, 158, 11, 0.6)'],
      borderColor: ['#8b5cf6', '#10b981', '#06b6d4', '#f59e0b'],
      borderWidth: 1
    }]
  } : null;

  return (
    <>
      <div className="header">
        <div>
          <h1>Performance Overview</h1>
          <p>Core business metrics and sales distributions</p>
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
          <LoadingState message="Loading Dashboard Metrics..." />
        ) : isError ? (
          <ErrorState message={error instanceof Error ? error.message : 'Unknown error'} onRetry={() => refetch()} />
        ) : (
          <>
            <DashboardKpiCards kpis={data?.kpis || null} />

            <div className="charts-grid">
              <div className="chart-card">
                <h3><Package size={16} /> Campaign Marketing Mix</h3>
                <div style={{ height: '260px', position: 'relative', display: 'flex', justifyContent: 'center' }}>
                  {campaignChartConfig ? (
                    <Bar 
                      data={campaignChartConfig}
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
                  ) : <p>No Campaign Data Available</p>}
                </div>
              </div>

              <div className="chart-card">
                <h3><Users size={16} /> Sales Channel Split</h3>
                <div style={{ height: '220px', position: 'relative', display: 'flex', justifyContent: 'center' }}>
                  {channelChartConfig ? (
                    <Doughnut 
                      data={channelChartConfig}
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                          legend: { position: 'bottom', labels: { color: '#9ca3af', font: { family: 'Outfit' }, boxWidth: 12 } }
                        }
                      }}
                    />
                  ) : <p>No Channel Data Available</p>}
                </div>
              </div>
            </div>

            {selectedProduct && data?.inventoryData && (
              <div className="chart-card animate-fade-in" style={{ marginBottom: '28px' }}>
                <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Package size={16} /> Product Inventory & Stockout Assessment ({selectedProduct})
                </h3>
                <div className="trend-stats" style={{ margin: '0' }}>
                  <div className="trend-stat-card">
                    <label>Current Stock</label>
                    <p>{formatNumber(data.inventoryData.current_stock)} units</p>
                  </div>
                  <div className="trend-stat-card">
                    <label>Average Period Stock</label>
                    <p>{formatNumber(data.inventoryData.average_stock.toFixed(0))}</p>
                  </div>
                  <div className="trend-stat-card">
                    <label>Estimated Coverage</label>
                    <p>{data.inventoryData.estimated_days_of_stock.toFixed(1)} days</p>
                  </div>
                  <div className="trend-stat-card" style={{ 
                    borderColor: data.inventoryData.stockout_risk === 'High' ? 'rgba(239, 68, 68, 0.4)' : 
                                 data.inventoryData.stockout_risk === 'Medium' ? 'rgba(245, 158, 11, 0.4)' : 'rgba(16, 185, 129, 0.4)'
                  }}>
                    <label>Stockout Risk</label>
                    <p style={{ 
                      color: data.inventoryData.stockout_risk === 'High' ? 'var(--danger)' : 
                             data.inventoryData.stockout_risk === 'Medium' ? 'var(--warning)' : 'var(--success)'
                    }}>
                      {data.inventoryData.stockout_risk}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </>
  );
}
