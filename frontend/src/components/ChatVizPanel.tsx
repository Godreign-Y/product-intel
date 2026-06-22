import React from 'react';
import { Bar, Line, Doughnut } from 'react-chartjs-2';
import 'chart.js/auto';
import { useTheme } from '../context/ThemeContext';
import { getChartLegend, getChartScales } from '../utils/chartTheme';
import { ChatVisualization } from '../types';

const MUTED_PALETTE = ['#7A7268', '#A89E8E', '#524C44', '#C9BFB0', '#6B8F96'];

interface ChatVizPanelProps {
  visualizations: ChatVisualization[];
}

function applyMutedPalette(data: ChatVisualization['data']) {
  if (!data?.datasets) return data;
  return {
    ...data,
    datasets: data.datasets.map((ds: Record<string, unknown>, i: number) => ({
      ...ds,
      backgroundColor: Array.isArray(ds.backgroundColor)
        ? (ds.backgroundColor as string[]).map((_, j) => MUTED_PALETTE[j % MUTED_PALETTE.length])
        : MUTED_PALETTE[i % MUTED_PALETTE.length],
      borderColor: MUTED_PALETTE[i % MUTED_PALETTE.length],
      borderWidth: ds.borderWidth ?? 1.5,
      pointBackgroundColor: MUTED_PALETTE[0],
      pointBorderColor: 'transparent',
    })),
  };
}

function VizChart({ viz }: { viz: ChatVisualization }) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const scales = getChartScales(isDark);
  const legend = getChartLegend(isDark);

  if (viz.status === 'loading' || !viz.data) {
    return (
      <div className="chat-viz-card chat-viz-card--loading">
        <div className="chat-viz-card__header">
          <span className="chat-viz-card__title">{viz.title}</span>
          {viz.subtitle && <span className="chat-viz-card__subtitle">{viz.subtitle}</span>}
        </div>
        <div className="chat-viz-card__loader">
          <div style={{ width: '100%' }}>
            <div className="chat-viz-skeleton chat-viz-skeleton--wide" />
            <div className="chat-viz-skeleton chat-viz-skeleton--mid" style={{ marginTop: 12 }} />
            <div className="chat-viz-skeleton chat-viz-skeleton--chart" />
          </div>
          <span>Building chart…</span>
        </div>
      </div>
    );
  }

  if (viz.status === 'error') {
    return (
      <div className="chat-viz-card chat-viz-card--error">
        <div className="chat-viz-card__header">
          <span className="chat-viz-card__title">{viz.title}</span>
        </div>
        <p className="chat-viz-card__error">This chart could not be rendered.</p>
      </div>
    );
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: viz.index_axis === 'y' ? ('y' as const) : ('x' as const),
    plugins: {
      legend: viz.chart_type === 'doughnut' ? legend : { display: false },
      tooltip: { enabled: true, padding: 12, cornerRadius: 8 },
    },
    scales: viz.chart_type === 'doughnut' ? undefined : scales,
  };

  const chartData = applyMutedPalette(viz.data);

  return (
    <div className="chat-viz-card">
      <div className="chat-viz-card__header">
        <span className="chat-viz-card__title">{viz.title}</span>
        {viz.subtitle && <span className="chat-viz-card__subtitle">{viz.subtitle}</span>}
      </div>
      <div className="chat-viz-card__canvas">
        {viz.chart_type === 'line' && <Line data={chartData} options={options} />}
        {viz.chart_type === 'bar' && <Bar data={chartData} options={options} />}
        {viz.chart_type === 'doughnut' && <Doughnut data={chartData} options={options} />}
      </div>
    </div>
  );
}

export default function ChatVizPanel({ visualizations }: ChatVizPanelProps) {
  if (!visualizations.length) return null;

  return (
    <div className="chat-viz-gallery">
      {visualizations.map((viz) => (
        <VizChart key={viz.id} viz={viz} />
      ))}
    </div>
  );
}
