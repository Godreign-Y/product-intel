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
    'rgba(165, 90, 50, 0.7)', // Or ideally use themeConfig if we want alpha. I'll stick to a mix for now, but Chart.js works better with hex/rgba strings. Let's use the actual themeConfig palette.
    'rgba(11, 36, 32, 0.6)',
    'rgba(205, 176, 141, 0.7)',
    'rgba(107, 158, 120, 0.6)',
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
