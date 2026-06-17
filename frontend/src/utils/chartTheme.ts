/** Chart.js theme helpers aligned with Calm palette */

export const CHART_COLORS = {
  sienna: '#A55A32',
  bush: '#0B2420',
  oak: '#CDB08D',
  cashmere: '#E7DED2',
  siennaAlpha: 'rgba(165, 90, 50, 0.12)',
  oakAlpha: 'rgba(205, 176, 141, 0.35)',
  palette: ['#A55A32', '#0B2420', '#CDB08D', '#6B9E78', '#8B7355'],
  paletteAlpha: [
    'rgba(165, 90, 50, 0.7)',
    'rgba(11, 36, 32, 0.6)',
    'rgba(205, 176, 141, 0.7)',
    'rgba(107, 158, 120, 0.6)',
  ],
};

export function getChartScales(isDark: boolean) {
  const tick = isDark ? 'rgba(231, 222, 210, 0.5)' : 'rgba(11, 36, 32, 0.45)';
  const grid = isDark ? 'rgba(231, 222, 210, 0.06)' : 'rgba(11, 36, 32, 0.06)';
  return {
    y: {
      ticks: { color: tick, font: { family: 'IBM Plex Sans', size: 11 } },
      grid: { color: grid, drawBorder: false },
      border: { display: false },
    },
    x: {
      ticks: { color: tick, font: { family: 'IBM Plex Sans', size: 11 } },
      grid: { display: false },
      border: { display: false },
    },
  };
}

export function getChartLegend(isDark: boolean) {
  return {
    position: 'bottom' as const,
    labels: {
      color: isDark ? 'rgba(231, 222, 210, 0.65)' : 'rgba(11, 36, 32, 0.6)',
      font: { family: 'IBM Plex Sans', size: 12 },
      boxWidth: 10,
      padding: 16,
      usePointStyle: true,
      pointStyle: 'circle' as const,
    },
  };
}
