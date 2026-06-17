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
import { Button } from '../components/ui/Button';
import { Card, CardHeader } from '../components/ui/Card';
import { DashboardSkeleton } from '../components/ui/Skeleton';
import { useTheme } from '../context/ThemeContext';
import { CHART_COLORS, getChartScales, getChartLegend } from '../utils/chartTheme';

export default function DashboardPage() {
  const { selectedProduct, selectedCategory, startDate, endDate } = useFilters();
  const { theme } = useTheme();

  const { data, isLoading, isError, error, refetch, isFetching } = useDashboard({
    product_id: selectedProduct || null,
    category: selectedCategory || null,
    start_date: startDate || null,
    end_date: endDate || null,
  });

  const isDark = theme === 'dark';
  const scales = getChartScales(isDark);
  const legend = getChartLegend(isDark);

  const campaignChartConfig = data?.campaignData?.campaign_mix
    ? {
        labels: Object.keys(data.campaignData.campaign_mix),
        datasets: [
          {
            label: 'Campaign Mix (%)',
            data: Object.values(data.campaignData.campaign_mix).map((v: unknown) => (v as number) * 100),
            backgroundColor: CHART_COLORS.paletteAlpha,
            borderColor: CHART_COLORS.palette,
            borderWidth: 1.5,
            borderRadius: 8,
          },
        ],
      }
    : null;

  const channelChartConfig = data?.channelData?.channel_mix
    ? {
        labels: Object.keys(data.channelData.channel_mix),
        datasets: [
          {
            data: Object.values(data.channelData.channel_mix).map((v: unknown) => (v as number) * 100),
            backgroundColor: CHART_COLORS.palette,
            borderWidth: 0,
            hoverOffset: 8,
            spacing: 2,
          },
        ],
      }
    : null;

  return (
    <>
      <header className="page-header">
        <div className="page-header-text">
          <h1>Performance Overview</h1>
          <p>Executive summary of core business metrics and channel distributions</p>
        </div>
        <div className="page-header-actions">
          <Button
            variant="ghost"
            size="sm"
            icon={<RefreshCw size={14} className={isFetching ? 'spin' : ''} />}
            onClick={() => refetch()}
            disabled={isFetching}
          >
            Sync Data
          </Button>
        </div>
      </header>

      <GlobalFilterBar />

      <div className="animate-fade-in">
        {isLoading ? (
          <DashboardSkeleton />
        ) : isError ? (
          <ErrorState
            message={error instanceof Error ? error.message : 'Unknown error'}
            onRetry={() => refetch()}
          />
        ) : (
          <>
            <DashboardKpiCards kpis={data?.kpis || null} />

            <div className="bento-grid">
              <Card variant="elevated" padding="lg" className="bento-wide">
                <CardHeader
                  title="Campaign Marketing Mix"
                  subtitle="Spend allocation across channels"
                  icon={<Package size={18} />}
                />
                <div className="chart-container">
                  {campaignChartConfig ? (
                    <Bar
                      data={campaignChartConfig}
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: { legend: { display: false } },
                        scales,
                      }}
                    />
                  ) : (
                    <div className="empty-state" style={{ padding: 'var(--space-10)' }}>
                      <p>No campaign data available</p>
                    </div>
                  )}
                </div>
              </Card>

              <Card variant="elevated" padding="lg">
                <CardHeader
                  title="Sales Channel Split"
                  subtitle="Revenue distribution"
                  icon={<Users size={18} />}
                />
                <div className="chart-container-sm">
                  {channelChartConfig ? (
                    <Doughnut
                      data={channelChartConfig}
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        cutout: '68%',
                        plugins: { legend },
                      }}
                    />
                  ) : (
                    <div className="empty-state" style={{ padding: 'var(--space-10)' }}>
                      <p>No channel data available</p>
                    </div>
                  )}
                </div>
              </Card>
            </div>

            {selectedProduct && data?.inventoryData && (
              <Card variant="glass" padding="lg" className="animate-fade-in-scale">
                <CardHeader
                  title={`Inventory Assessment · ${selectedProduct}`}
                  subtitle="Stock levels and stockout risk analysis"
                  icon={<Package size={18} />}
                />
                <div className="trend-stats" style={{ margin: 0 }}>
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
                  <div
                    className="trend-stat-card"
                    style={{
                      borderColor:
                        data.inventoryData.stockout_risk === 'High'
                          ? 'rgba(196, 92, 74, 0.35)'
                          : data.inventoryData.stockout_risk === 'Medium'
                            ? 'rgba(165, 90, 50, 0.35)'
                            : 'rgba(107, 158, 120, 0.35)',
                    }}
                  >
                    <label>Stockout Risk</label>
                    <p
                      style={{
                        color:
                          data.inventoryData.stockout_risk === 'High'
                            ? 'var(--danger)'
                            : data.inventoryData.stockout_risk === 'Medium'
                              ? 'var(--calm-sienna)'
                              : 'var(--success)',
                      }}
                    >
                      {data.inventoryData.stockout_risk}
                    </p>
                  </div>
                </div>
              </Card>
            )}
          </>
        )}
      </div>
    </>
  );
}
