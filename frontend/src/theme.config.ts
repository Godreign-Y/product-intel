export type ThemeMode = 'light' | 'dark';

export interface ThemeConfig {
  palette: {
    sienna: string;
    siennaLight: string;
    siennaMuted: string;
    cashmere: string;
    cashmereDark: string;
    cashmereLightMode: string;
    oak: string;
    oakLight: string;
    oakLightMode: string;
    oakMuted: string;
    bush: string;
    bushLight: string;
    bushDeep: string;
    bushElevated: string;
    bushSurface: string;
    charcoal: string;
    charcoalLight: string;
    success: string;
    danger: string;
  };
  typography: {
    fontDisplay: string;
    fontBody: string;
    fontMono: string;
    sizes: Record<string, string>;
    leading: Record<string, string>;
    weights: Record<string, string>;
  };
  spacing: Record<string, string>;
  radius: Record<string, string>;
  motion: Record<string, string>;
  themes: {
    light: ThemeColors;
    dark: ThemeColors;
  };
}

export interface ThemeColors {
  bgBase: string;
  bgElevated: string;
  bgSurface: string;
  bgSurfaceHover: string;
  bgCard: string;
  bgCardHover: string;
  bgGlass: string;
  bgInput: string;
  
  textPrimary: string;
  textSecondary: string;
  textMuted: string;
  textInverse: string;
  
  borderSubtle: string;
  borderDefault: string;
  borderStrong: string;
  borderFocus: string;
  
  accentPrimary: string;
  accentPrimaryHover: string;
  accentSecondary: string;
  accentSienna: string;
  
  shadowXs: string;
  shadowSm: string;
  shadowMd: string;
  shadowLg: string;
  shadowFloat: string;
  shadowGlowSienna: string;
  
  textureOverlay: string;
  
  success: string;
  successBg: string;
  warning: string;
  warningBg: string;
  danger: string;
  dangerBg: string;
  info: string;
  infoBg: string;
  
  sidebarBg: string;
  sidebarActive: string;
  sidebarActiveIndicator: string;

  chartSienna: string;
  chartBush: string;
  chartOak: string;
  chartCashmere: string;
  chartSiennaAlpha: string;
  chartOakAlpha: string;
  
  // Specifically for the body texture radial gradients
  bodyGradient1: string;
  bodyGradient2: string;
}

export const themeConfig: ThemeConfig = {
  palette: {
    sienna: '#A55A32',
    siennaLight: '#C4784F',
    siennaMuted: 'rgba(165, 90, 50, 0.15)',
    cashmere: '#E7DED2',
    cashmereDark: '#D5C8B6',
    cashmereLightMode: '#F7F5F0',
    oak: '#CDB08D',
    oakLight: '#E2D6C0',
    oakLightMode: '#ECE9E2',
    oakMuted: 'rgba(205, 176, 141, 0.25)',
    bush: '#181C14',
    bushLight: '#2C3326',
    bushDeep: '#10130D',
    bushElevated: '#1C2017',
    bushSurface: '#262C20',
    charcoal: '#2D3237',
    charcoalLight: '#3A4046',
    success: '#6B9E78',
    danger: '#C45C4A',
  },
  typography: {
    fontDisplay: "'Outfit', -apple-system, 'Segoe UI', system-ui, sans-serif",
    fontBody: "'Plus Jakarta Sans', -apple-system, 'Segoe UI', system-ui, sans-serif",
    fontMono: "'SF Mono', 'JetBrains Mono', monospace",
    sizes: {
      xs: '0.75rem',
      sm: '0.875rem',
      base: '1rem',
      lg: '1.125rem',
      xl: '1.25rem',
      '2xl': '1.5rem',
      '3xl': '2rem',
      '4xl': '2.75rem',
      '5xl': '3.5rem',
    },
    leading: {
      tight: '1.15',
      normal: '1.5',
      relaxed: '1.75',
    },
    weights: {
      light: '300',
      regular: '400',
      medium: '500',
      semibold: '600',
    },
  },
  spacing: {
    '1': '4px',
    '2': '8px',
    '3': '12px',
    '4': '16px',
    '5': '20px',
    '6': '24px',
    '8': '32px',
    '10': '40px',
    '12': '48px',
    '16': '64px',
    '20': '80px',
    '24': '96px',
  },
  radius: {
    sm: '10px',
    md: '16px',
    lg: '20px',
    xl: '24px',
    full: '9999px',
  },
  motion: {
    transitionFast: '200ms cubic-bezier(0.4, 0, 0.2, 1)',
    transitionBase: '300ms cubic-bezier(0.4, 0, 0.2, 1)',
    transitionSlow: '350ms cubic-bezier(0.4, 0, 0.2, 1)',
    easeOutExpo: 'cubic-bezier(0.16, 1, 0.3, 1)',
  },
  themes: {
    dark: {
      bgBase: 'var(--calm-bush-deep)',
      bgElevated: 'var(--calm-bush-elevated)',
      bgSurface: 'rgba(26, 53, 48, 0.55)',
      bgSurfaceHover: 'rgba(26, 53, 48, 0.75)',
      bgCard: 'rgba(231, 222, 210, 0.05)',
      bgCardHover: 'rgba(231, 222, 210, 0.08)',
      bgGlass: 'rgba(14, 33, 29, 0.82)',
      bgInput: 'rgba(11, 36, 32, 0.65)',
      textPrimary: 'var(--calm-cashmere)',
      textSecondary: 'rgba(231, 222, 210, 0.65)',
      textMuted: 'rgba(231, 222, 210, 0.4)',
      textInverse: 'var(--calm-cashmere)',
      borderSubtle: 'rgba(231, 222, 210, 0.08)',
      borderDefault: 'rgba(231, 222, 210, 0.12)',
      borderStrong: 'rgba(231, 222, 210, 0.2)',
      borderFocus: 'var(--calm-sienna)',
      accentPrimary: 'var(--calm-bush)',
      accentPrimaryHover: 'var(--calm-bush-light)',
      accentSecondary: 'var(--calm-cashmere)',
      accentSienna: 'var(--calm-sienna)',
      shadowXs: '0 1px 2px rgba(0, 0, 0, 0.2)',
      shadowSm: '0 2px 8px rgba(0, 0, 0, 0.15)',
      shadowMd: '0 8px 24px rgba(0, 0, 0, 0.2)',
      shadowLg: '0 16px 48px rgba(0, 0, 0, 0.25)',
      shadowFloat: '0 20px 60px rgba(0, 0, 0, 0.3), 0 0 0 1px var(--border-subtle)',
      shadowGlowSienna: '0 0 40px rgba(165, 90, 50, 0.15)',
      textureOverlay: "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E\")",
      success: '#6B9E78',
      successBg: 'rgba(107, 158, 120, 0.12)',
      warning: 'var(--calm-sienna-light)',
      warningBg: 'var(--calm-sienna-muted)',
      danger: '#C45C4A',
      dangerBg: 'rgba(196, 92, 74, 0.12)',
      info: 'var(--calm-oak)',
      infoBg: 'var(--calm-oak-muted)',
      sidebarBg: 'rgba(11, 36, 32, 0.92)',
      sidebarActive: 'rgba(165, 90, 50, 0.14)',
      sidebarActiveIndicator: 'var(--calm-sienna)',
      chartSienna: '#A55A32',
      chartBush: '#0B2420',
      chartOak: '#CDB08D',
      chartCashmere: '#E7DED2',
      chartSiennaAlpha: 'rgba(165, 90, 50, 0.12)',
      chartOakAlpha: 'rgba(205, 176, 141, 0.35)',
      bodyGradient1: 'radial-gradient(ellipse 80% 50% at 10% 0%, rgba(165, 90, 50, 0.07) 0%, transparent 50%)',
      bodyGradient2: 'radial-gradient(ellipse 60% 40% at 90% 100%, rgba(11, 36, 32, 0.2) 0%, transparent 55%)'
    },
    light: {
      bgBase: 'var(--calm-cashmere-light-mode)',
      bgElevated: 'var(--calm-oak-light-mode)',
      bgSurface: 'rgba(255, 255, 255, 0.45)',
      bgSurfaceHover: 'rgba(255, 255, 255, 0.65)',
      bgCard: 'rgba(255, 255, 255, 0.5)',
      bgCardHover: 'rgba(255, 255, 255, 0.75)',
      bgGlass: 'rgba(255, 255, 255, 0.55)',
      bgInput: 'rgba(255, 255, 255, 0.7)',
      textPrimary: 'var(--calm-bush)',
      textSecondary: 'rgba(24, 28, 20, 0.65)',
      textMuted: 'rgba(24, 28, 20, 0.4)',
      textInverse: 'var(--calm-cashmere)',
      borderSubtle: 'rgba(165, 90, 50, 0.08)',
      borderDefault: 'rgba(165, 90, 50, 0.14)',
      borderStrong: 'rgba(165, 90, 50, 0.25)',
      borderFocus: 'var(--calm-sienna)',
      accentPrimary: 'var(--calm-bush)',
      accentPrimaryHover: 'var(--calm-bush-light)',
      accentSecondary: 'var(--calm-cashmere)',
      accentSienna: 'var(--calm-sienna)',
      shadowXs: '0 1px 2px rgba(165, 90, 50, 0.03)',
      shadowSm: '0 4px 16px rgba(165, 90, 50, 0.04)',
      shadowMd: '0 10px 30px rgba(165, 90, 50, 0.06)',
      shadowLg: '0 20px 50px rgba(165, 90, 50, 0.08)',
      shadowFloat: '0 24px 64px rgba(165, 90, 50, 0.08), 0 0 0 1px var(--border-subtle)',
      shadowGlowSienna: '0 0 40px rgba(165, 90, 50, 0.08)',
      textureOverlay: "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.025'/%3E%3C/svg%3E\")",
      success: '#6B9E78',
      successBg: 'rgba(107, 158, 120, 0.12)',
      warning: 'var(--calm-sienna-light)',
      warningBg: 'var(--calm-sienna-muted)',
      danger: '#C45C4A',
      dangerBg: 'rgba(196, 92, 74, 0.12)',
      info: 'var(--calm-oak)',
      infoBg: 'var(--calm-oak-muted)',
      sidebarBg: 'rgba(247, 245, 240, 0.65)',
      sidebarActive: 'rgba(165, 90, 50, 0.1)',
      sidebarActiveIndicator: 'var(--calm-sienna)',
      chartSienna: '#A55A32',
      chartBush: '#0B2420',
      chartOak: '#CDB08D',
      chartCashmere: '#E7DED2',
      chartSiennaAlpha: 'rgba(165, 90, 50, 0.12)',
      chartOakAlpha: 'rgba(205, 176, 141, 0.35)',
      bodyGradient1: 'radial-gradient(ellipse 80% 50% at 10% 0%, rgba(165, 90, 50, 0.05) 0%, transparent 60%)',
      bodyGradient2: 'radial-gradient(ellipse 60% 40% at 90% 100%, rgba(205, 176, 141, 0.15) 0%, transparent 60%)'
    }
  }
};
