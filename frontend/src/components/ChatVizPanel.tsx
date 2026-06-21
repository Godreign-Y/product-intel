import React from 'react';
import { Bar, Line, Doughnut } from 'react-chartjs-2';
import 'chart.js/auto';
import { RefreshCw } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { getChartLegend, getChartScales } from '../utils/chartTheme';
import { ChatVisualization } from '../types';

interface ChatVizPanelProps {
  visualizations: ChatVisualization[];
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
          <RefreshCw size={16} className="spin" />
          <span>Rendering chart…</span>
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
        <p className="chat-viz-card__error">Could not render this chart.</p>
      </div>
    );
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: viz.index_axis === 'y' ? ('y' as const) : ('x' as const),
    plugins: { legend, tooltip: { enabled: true } },
    scales: viz.chart_type === 'doughnut' ? undefined : scales,
  };

  const chartData = viz.data;

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
      {visualizations.map(viz => (
        <VizChart key={viz.id} viz={viz} />
      ))}
    </div>
  );
}
