import { themeConfig } from '../theme.config';

/** Chart.js theme helpers aligned with Calm palette */

export const CHART_COLORS = {
  sienna: themeConfig.palette.sienna,
  bush: themeConfig.palette.bush,
  oak: themeConfig.palette.oak,
  cashmere: themeConfig.palette.cashmere,
  siennaAlpha: themeConfig.palette.siennaMuted,
  oakAlpha: themeConfig.palette.oakMuted,
  palette: [
    themeConfig.palette.sienna, 
    themeConfig.palette.bush, 
    themeConfig.palette.oak, 
    themeConfig.palette.success, 
    themeConfig.palette.danger // replaced hardcoded #8B7355 with danger for consistency
  ],
  paletteAlpha: [
    'rgba(122, 114, 104, 0.65)',
    'rgba(82, 76, 68, 0.55)',
    'rgba(201, 191, 176, 0.65)',
    'rgba(107, 143, 150, 0.55)',
  ],
};

export function getChartScales(isDark: boolean) {
  const theme = isDark ? themeConfig.themes.dark : themeConfig.themes.light;
  const tick = isDark ? 'rgba(231, 222, 210, 0.5)' : 'rgba(11, 36, 32, 0.45)'; // we can replace with theme.textMuted
  const grid = isDark ? 'rgba(231, 222, 210, 0.06)' : 'rgba(11, 36, 32, 0.06)'; // theme.borderSubtle
  
  return {
    y: {
      ticks: { color: theme.textMuted, font: { family: themeConfig.typography.fontBody, size: 11 } },
      grid: { color: theme.borderSubtle, drawBorder: false },
      border: { display: false },
    },
    x: {
      ticks: { color: theme.textMuted, font: { family: themeConfig.typography.fontBody, size: 11 } },
      grid: { display: false },
      border: { display: false },
    },
  };
}

export function getChartLegend(isDark: boolean) {
  const theme = isDark ? themeConfig.themes.dark : themeConfig.themes.light;
  return {
    position: 'bottom' as const,
    labels: {
      color: theme.textSecondary,
      font: { family: themeConfig.typography.fontBody, size: 12 },
      boxWidth: 10,
      padding: 16,
      usePointStyle: true,
      pointStyle: 'circle' as const,
    },
  };
}
