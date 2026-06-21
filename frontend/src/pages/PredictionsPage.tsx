import React, { useState } from 'react';
import { Line } from 'react-chartjs-2';
import 'chart.js/auto';
import { ArrowUpRight, ArrowDownRight, RefreshCw, TrendingUp } from 'lucide-react';
import { useFilters } from '../components/FilterContext';
import { GlobalFilterBar } from '../components/GlobalFilterBar';
import { usePredictions } from '../hooks/usePredictions';
import { LoadingState, ErrorState } from '../components/LoadingErrorState';
import { Button } from '../components/ui/Button';
import { Card, CardHeader } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Table } from '../components/ui/Table';
import { useTheme } from '../context/ThemeContext';
import { CHART_COLORS, getChartScales } from '../utils/chartTheme';
import { themeConfig } from '../theme.config';

export default function PredictionsPage() {
  const { selectedProduct, selectedCategory, startDate, endDate } = useFilters();
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const [trendMetric, setTrendMetric] = useState('revenue');
  const [trendGranularity, setTrendGranularity] = useState('daily');

  const { data, isLoading, isError, error, refetch, isFetching } = usePredictions({
    product_id: selectedProduct || null,
    category: selectedCategory || null,
    start_date: startDate || null,
    end_date: endDate || null,
    metric: trendMetric,
    granularity: trendGranularity,
  });

  const trendData = data?.data;
  const scales = getChartScales(isDark);

  const trendChartConfig = trendData?.history
    ? {
        labels: trendData.history.map(pt => pt.date),
        datasets: [
          {
            label: trendMetric.replace('_', ' '),
            data: trendData.history.map(pt => pt.value),
            borderColor: CHART_COLORS.sienna,
            backgroundColor: CHART_COLORS.siennaAlpha,
            borderWidth: 2.5,
            tension: 0.42,
            fill: true,
            pointRadius: trendData.history.length > 30 ? 0 : 4,
            pointHoverRadius: 6,
            pointBackgroundColor: CHART_COLORS.sienna,
            pointBorderColor: isDark ? CHART_COLORS.cashmere : themeConfig.palette.cashmereLightMode,
            pointBorderWidth: 2,
          },
        ],
      }
    : null;

  const tableData =
    trendData?.history?.slice(-8).map(pt => ({
      date: pt.date,
      value: typeof pt.value === 'number' ? pt.value.toFixed(2) : pt.value,
      metric: trendMetric.replace('_', ' '),
    })) ?? [];

  return (
    <>
      <header className="page-header">
        <div className="page-header-text">
          <h1>Analytics</h1>
          <p>Longitudinal tracking, regression analysis, and metric trajectories</p>
        </div>
        <div className="page-header-actions">
          <Button
            variant="ghost"
            size="sm"
            icon={<RefreshCw size={14} className={isFetching ? 'spin' : ''} />}
            onClick={() => refetch()}
            disabled={isFetching}
          >
            Refresh
          </Button>
        </div>
      </header>

      <GlobalFilterBar />

      <div className="animate-fade-in">
        {isLoading ? (
          <LoadingState message="Analyzing time-series models..." />
        ) : isError ? (
          <ErrorState
            message={error instanceof Error ? error.message : 'Unknown error'}
            onRetry={() => refetch()}
          />
        ) : (
          <>
            {trendData && (
              <div className="analytics-hero animate-fade-in-scale">
                <div>
                  <Badge variant="sienna">{trendGranularity}</Badge>
                  <h2 style={{ marginTop: 'var(--space-3)', fontSize: 'var(--text-2xl)' }}>
                    {trendMetric.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())} Trajectory
                  </h2>
                  <p style={{ color: 'var(--text-muted)', marginTop: 'var(--space-2)' }}>
                    Regression analysis over selected period
                  </p>
                </div>
                <div className="analytics-hero-stat">
                  <label>Period Growth</label>
                  <p
                    style={{
                      color:
                        (trendData.growth_rate_pct || 0) > 0
                          ? 'var(--success)'
                          : (trendData.growth_rate_pct || 0) < 0
                            ? 'var(--danger)'
                            : undefined,
                    }}
                  >
                    {(trendData.growth_rate_pct || 0) > 0 ? '+' : ''}
                    {trendData.growth_rate_pct}%
                  </p>
                </div>
              </div>
            )}

            <Card variant="elevated" padding="lg" style={{ marginBottom: 'var(--space-8)' }}>
              <div className="trends-config">
                <CardHeader
                  title={`Metric Trajectory`}
                  subtitle={trendMetric.replace('_', ' ').toUpperCase()}
                  icon={<TrendingUp size={18} />}
                />
                <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
                  <select
                    className="filter-select"
                    value={trendMetric}
                    onChange={e => setTrendMetric(e.target.value)}
                    style={{ minWidth: 160 }}
                  >
                    <option value="revenue">Revenue</option>
                    <option value="orders">Orders</option>
                    <option value="conversion_rate">Conversion Rate</option>
                    <option value="retention_rate">Retention Rate</option>
                  </select>
                  <div className="granularity-selector">
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

              <div style={{ height: 380, position: 'relative' }}>
                {trendChartConfig ? (
                  <Line
                    data={trendChartConfig}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: { legend: { display: false } },
                      scales,
                      interaction: { intersect: false, mode: 'index' },
                    }}
                  />
                ) : (
                  <div className="empty-state">
                    <div className="empty-state-icon">
                      <TrendingUp size={28} />
                    </div>
                    <h3>No trend data available</h3>
                    <p>Adjust your filters or date range to view analytics</p>
                  </div>
                )}
              </div>

              {trendData && (
                <div className="trend-stats animate-fade-in">
                  <div className="trend-stat-card">
                    <label>Direction</label>
                    <p
                      style={{
                        color:
                          trendData.direction === 'increasing'
                            ? 'var(--success)'
                            : trendData.direction === 'decreasing'
                              ? 'var(--danger)'
                              : undefined,
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6,
                      }}
                    >
                      {trendData.direction === 'increasing' && <ArrowUpRight size={18} />}
                      {trendData.direction === 'decreasing' && <ArrowDownRight size={18} />}
                      {trendData.direction?.toUpperCase()}
                    </p>
                  </div>
                  <div className="trend-stat-card">
                    <label>Growth Rate</label>
                    <p
                      style={{
                        color:
                          (trendData.growth_rate_pct || 0) > 0
                            ? 'var(--success)'
                            : (trendData.growth_rate_pct || 0) < 0
                              ? 'var(--danger)'
                              : undefined,
                      }}
                    >
                      {(trendData.growth_rate_pct || 0) > 0 ? '+' : ''}
                      {trendData.growth_rate_pct}%
                    </p>
                  </div>
                  <div className="trend-stat-card">
                    <label>R-Squared Fit</label>
                    <p>{((trendData.r_squared || 0) * 100).toFixed(2)}%</p>
                  </div>
                  <div className="trend-stat-card">
                    <label>Statistical Significance</label>
                    <p>{(trendData.p_value || 1) < 0.05 ? 'Significant' : 'Weak effect'}</p>
                  </div>
                </div>
              )}
            </Card>

            {tableData.length > 0 && (
              <Card variant="default" padding="lg">
                <CardHeader title="Recent Data Points" subtitle="Latest period values" />
                <Table
                  columns={[
                    { key: 'date', header: 'Date', sortable: true },
                    { key: 'metric', header: 'Metric' },
                    { key: 'value', header: 'Value', sortable: true },
                  ]}
                  data={tableData}
                />
              </Card>
            )}
          </>
        )}
      </div>
    </>
  );
}
