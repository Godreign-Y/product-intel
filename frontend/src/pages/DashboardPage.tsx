import React from 'react';
import { Bar, Doughnut } from 'react-chartjs-2';
import 'chart.js/auto';
import { Package, Users, RefreshCw, LayoutGrid } from 'lucide-react';
import { useFilters } from '../components/FilterContext';
import { GlobalFilterBar } from '../components/GlobalFilterBar';
import { DashboardKpiCards } from '../components/DashboardKpiCards';
import { formatNumber } from '../utils/formatters';
import { useDashboard } from '../hooks/useDashboard';
import { LoadingState, ErrorState } from '../components/LoadingErrorState';
import { Button } from '../components/ui/Button';
import { CardHeader } from '../components/ui/Card';
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
            backgroundColor: [
              'rgba(122, 114, 104, 0.75)',
              'rgba(168, 158, 142, 0.7)',
              'rgba(82, 76, 68, 0.65)',
              'rgba(201, 191, 176, 0.7)',
              'rgba(138, 143, 150, 0.65)',
            ],
            borderColor: 'transparent',
            borderWidth: 0,
            borderRadius: 12,
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
            backgroundColor: ['#7A7268', '#A89E8E', '#C9BFB0', '#524C44', '#6B8F96'],
            borderWidth: 0,
            hoverOffset: 10,
            spacing: 3,
          },
        ],
      }
    : null;

  return (
    <>
      <header className="pin-hero animate-fade-in">
        <div>
          <div className="pin-hero-eyebrow">
            <LayoutGrid size={14} />
            Performance board
          </div>
          <h1>Good to see you — here&apos;s what&apos;s moving</h1>
          <p className="pin-hero-desc">
            A curated snapshot of revenue, channels, and inventory. Pin the filters you care about and watch the story unfold.
          </p>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)', alignItems: 'flex-end' }}>
          <Button
            variant="ghost"
            size="sm"
            icon={<RefreshCw size={14} className={isFetching ? 'spin' : ''} />}
            onClick={() => refetch()}
            disabled={isFetching}
          >
            Sync data
          </Button>
          <div className="pin-hero-badge">
            <span>Live</span>
            <strong style={{ fontSize: 'var(--text-lg)' }}>{isFetching ? '…' : '●'}</strong>
          </div>
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
          <div className="pin-masonry">
            <DashboardKpiCards kpis={data?.kpis || null} />

            <div className="pin-card pin-card--pad-lg pin-chart-wide">
              <CardHeader
                title="Campaign mix"
                subtitle="Where your marketing spend lands"
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
                    <p>No campaign data for these filters yet</p>
                  </div>
                )}
              </div>
            </div>

            <div className="pin-card pin-card--pad-lg pin-chart-side">
              <CardHeader
                title="Channel split"
                subtitle="Revenue by sales channel"
                icon={<Users size={18} />}
              />
              <div className="chart-container-sm">
                {channelChartConfig ? (
                  <Doughnut
                    data={channelChartConfig}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      cutout: '62%',
                      plugins: { legend },
                    }}
                  />
                ) : (
                  <div className="empty-state" style={{ padding: 'var(--space-10)' }}>
                    <p>No channel data yet</p>
                  </div>
                )}
              </div>
            </div>

            {selectedProduct && data?.inventoryData && (
              <div className="pin-card pin-card--pad-lg pin-inventory animate-fade-in-scale">
                <CardHeader
                  title={`Inventory · ${selectedProduct}`}
                  subtitle="Stock levels and coverage at a glance"
                  icon={<Package size={18} />}
                />
                <div className="inventory-pins">
                  <div className="inventory-pin">
                    <label>Current stock</label>
                    <p>{formatNumber(data.inventoryData.current_stock)}</p>
                  </div>
                  <div className="inventory-pin">
                    <label>Period average</label>
                    <p>{formatNumber(data.inventoryData.average_stock.toFixed(0))}</p>
                  </div>
                  <div className="inventory-pin">
                    <label>Coverage</label>
                    <p>{data.inventoryData.estimated_days_of_stock.toFixed(1)} days</p>
                  </div>
                  <div
                    className="inventory-pin"
                    style={{
                      borderColor:
                        data.inventoryData.stockout_risk === 'High'
                          ? 'var(--danger-bg)'
                          : data.inventoryData.stockout_risk === 'Medium'
                            ? 'var(--warning-bg)'
                            : 'var(--success-bg)',
                    }}
                  >
                    <label>Stockout risk</label>
                    <p
                      style={{
                        color:
                          data.inventoryData.stockout_risk === 'High'
                            ? 'var(--danger)'
                            : data.inventoryData.stockout_risk === 'Medium'
                              ? 'var(--cozy-rose)'
                              : 'var(--success)',
                      }}
                    >
                      {data.inventoryData.stockout_risk}
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
}
