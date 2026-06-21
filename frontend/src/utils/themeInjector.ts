import { themeConfig, ThemeMode, ThemeColors } from '../theme.config';

function toKebabCase(str: string): string {
  return str.replace(/([a-z0-9]|(?=[A-Z]))([A-Z])/g, '$1-$2').toLowerCase();
}

export function injectThemeVariables(mode: ThemeMode) {
  const root = document.documentElement;

  // 1. Inject Base Palette
  Object.entries(themeConfig.palette).forEach(([key, value]) => {
    root.style.setProperty(`--calm-${toKebabCase(key)}`, value);
  });

  // 2. Inject Typography
  root.style.setProperty('--font-display', themeConfig.typography.fontDisplay);
  root.style.setProperty('--font-body', themeConfig.typography.fontBody);
  root.style.setProperty('--font-mono', themeConfig.typography.fontMono);
  
  Object.entries(themeConfig.typography.sizes).forEach(([key, value]) => {
    root.style.setProperty(`--text-${key}`, value);
  });
  
  Object.entries(themeConfig.typography.leading).forEach(([key, value]) => {
    root.style.setProperty(`--leading-${key}`, value);
  });
  
  Object.entries(themeConfig.typography.weights).forEach(([key, value]) => {
    root.style.setProperty(`--weight-${key}`, value);
  });

  // 3. Inject Spacing
  Object.entries(themeConfig.spacing).forEach(([key, value]) => {
    root.style.setProperty(`--space-${key}`, value);
  });

  // 4. Inject Radius
  Object.entries(themeConfig.radius).forEach(([key, value]) => {
    root.style.setProperty(`--radius-${key}`, value);
  });

  // 5. Inject Motion
  Object.entries(themeConfig.motion).forEach(([key, value]) => {
    root.style.setProperty(`--${toKebabCase(key)}`, value);
  });

  // 6. Inject Semantic Themes (Light / Dark)
  const themeVars = themeConfig.themes[mode];
  Object.entries(themeVars).forEach(([key, value]) => {
    root.style.setProperty(`--${toKebabCase(key)}`, value);
  });

  // Update data-theme
  root.setAttribute('data-theme', mode);
}
