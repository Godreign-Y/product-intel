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
    cashmereLightMode: '#D5C8B6',
    oak: '#CDB08D',
    oakLight: '#E2D6C0',
    oakLightMode: '#E2D6C0',
    oakMuted: 'rgba(205, 176, 141, 0.25)',
    bush: '#0B2420',
    bushLight: '#1A3D36',
    bushDeep: '#0E211D',
    bushElevated: '#152B26',
    bushSurface: '#1A3530',
    charcoal: '#2D3237',
    charcoalLight: '#3A4046',
    success: '#6B9E78',
    danger: '#C45C4A',
  },
  typography: {
    fontDisplay: "'IBM Plex Sans', -apple-system, 'Segoe UI', system-ui, sans-serif",
    fontBody: "'IBM Plex Sans', -apple-system, 'Segoe UI', system-ui, sans-serif",
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
      bgSurface: 'rgba(240, 232, 218, 0.72)',
      bgSurfaceHover: 'rgba(244, 237, 224, 0.9)',
      bgCard: 'rgba(250, 246, 238, 0.65)',
      bgCardHover: 'rgba(252, 249, 243, 0.85)',
      bgGlass: 'rgba(226, 214, 192, 0.78)',
      bgInput: 'rgba(252, 249, 243, 0.88)',
      textPrimary: 'var(--calm-bush)',
      textSecondary: 'rgba(11, 36, 32, 0.65)',
      textMuted: 'rgba(11, 36, 32, 0.4)',
      textInverse: 'var(--calm-cashmere)',
      borderSubtle: 'rgba(11, 36, 32, 0.06)',
      borderDefault: 'rgba(11, 36, 32, 0.1)',
      borderStrong: 'rgba(11, 36, 32, 0.18)',
      borderFocus: 'var(--calm-sienna)',
      accentPrimary: 'var(--calm-bush)',
      accentPrimaryHover: 'var(--calm-bush-light)',
      accentSecondary: 'var(--calm-cashmere)',
      accentSienna: 'var(--calm-sienna)',
      shadowXs: '0 1px 2px rgba(11, 36, 32, 0.04)',
      shadowSm: '0 2px 12px rgba(11, 36, 32, 0.06)',
      shadowMd: '0 8px 32px rgba(11, 36, 32, 0.08)',
      shadowLg: '0 16px 56px rgba(11, 36, 32, 0.1)',
      shadowFloat: '0 20px 60px rgba(11, 36, 32, 0.08), 0 0 0 1px var(--border-subtle)',
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
      sidebarBg: 'rgba(240, 232, 218, 0.82)',
      sidebarActive: 'rgba(165, 90, 50, 0.1)',
      sidebarActiveIndicator: 'var(--calm-sienna)',
      chartSienna: '#A55A32',
      chartBush: '#0B2420',
      chartOak: '#CDB08D',
      chartCashmere: '#E7DED2',
      chartSiennaAlpha: 'rgba(165, 90, 50, 0.12)',
      chartOakAlpha: 'rgba(205, 176, 141, 0.35)',
      bodyGradient1: 'radial-gradient(ellipse 80% 50% at 10% 0%, rgba(165, 90, 50, 0.05) 0%, transparent 50%)',
      bodyGradient2: 'radial-gradient(ellipse 60% 40% at 90% 100%, rgba(226, 214, 192, 0.35) 0%, transparent 55%)'
    }
  }
};
