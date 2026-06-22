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
    cozyLinen: string;
    cozyBlush: string;
    cozyRose: string;
    cozySage: string;
    stone100: string;
    stone200: string;
    stone300: string;
    stone400: string;
    stone500: string;
    nightAccent: string;
    nightWarm: string;
    nightWarmMuted: string;
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
  panelTexture: string;
  
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
    sienna: '#6B7F78',
    siennaLight: '#8A9E97',
    siennaMuted: 'rgba(107, 127, 120, 0.14)',
    cashmere: '#E4E8E6',
    cashmereDark: '#D0D8D4',
    cashmereLightMode: '#EBE6DC',
    oak: '#B5A898',
    oakLight: '#D4CCC0',
    oakLightMode: '#DDD4C6',
    oakMuted: 'rgba(181, 168, 152, 0.28)',
    bush: '#2A3438',
    bushLight: '#3A484E',
    bushDeep: '#121A1C',
    bushElevated: '#1E2A2E',
    bushSurface: '#2A3840',
    charcoal: '#2E3638',
    charcoalLight: '#424C50',
    success: '#6E8F7A',
    danger: '#9A7068',
    cozyLinen: '#EBE6DC',
    cozyBlush: '#E6E1D8',
    cozyRose: '#8A8074',
    cozySage: '#6B8F82',
    cozyMauve: '#A8A4A0',
    stone100: '#EEE9E1',
    stone200: '#E8E3DA',
    stone300: '#E0DBD2',
    stone400: '#A89E8E',
    stone500: '#7A7268',
    stone600: '#524C44',
    nightAccent: '#5A9AAF',
    nightAccentSoft: '#4A8494',
    nightWarm: '#D4C48E',
    nightWarmMuted: 'rgba(212, 196, 142, 0.14)',
  },
  typography: {
    fontDisplay: "'Newsreader', Georgia, 'Times New Roman', serif",
    fontBody: "'Inter', -apple-system, 'Segoe UI', system-ui, sans-serif",
    fontMono: "'SF Mono', 'JetBrains Mono', monospace",
    sizes: {
      xs: '0.8125rem',
      sm: '0.9375rem',
      base: '1.0625rem',
      lg: '1.1875rem',
      xl: '1.3125rem',
      '2xl': '1.625rem',
      '3xl': '2.125rem',
      '4xl': '2.625rem',
      '5xl': '3.25rem',
    },
    leading: {
      tight: '1.25',
      normal: '1.55',
      relaxed: '1.7',
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
    '5': '22px',
    '6': '28px',
    '8': '36px',
    '10': '48px',
    '12': '56px',
    '16': '72px',
    '20': '96px',
    '24': '120px',
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
      bgBase: '#141C1E',
      bgElevated: '#1A2428',
      bgSurface: '#1E2A2E',
      bgSurfaceHover: '#243238',
      bgCard: '#222E32',
      bgCardHover: '#28363A',
      bgGlass: 'rgba(22, 32, 36, 0.9)',
      bgInput: 'rgba(18, 28, 32, 0.94)',
      textPrimary: '#E2E8DC',
      textSecondary: 'rgba(210, 218, 204, 0.72)',
      textMuted: 'rgba(176, 188, 176, 0.52)',
      textInverse: '#121A1C',
      borderSubtle: 'rgba(142, 180, 188, 0.1)',
      borderDefault: 'rgba(142, 180, 188, 0.16)',
      borderStrong: 'rgba(142, 180, 188, 0.26)',
      borderFocus: 'var(--calm-night-accent)',
      accentPrimary: 'var(--calm-bush-surface)',
      accentPrimaryHover: 'var(--calm-bush-light)',
      accentSecondary: 'var(--calm-cashmere)',
      accentSienna: 'var(--calm-night-warm)',
      shadowXs: '0 1px 2px rgba(0, 0, 0, 0.25)',
      shadowSm: '0 2px 8px rgba(0, 0, 0, 0.2)',
      shadowMd: '0 8px 24px rgba(0, 0, 0, 0.28)',
      shadowLg: '0 16px 48px rgba(0, 0, 0, 0.32)',
      shadowFloat: '0 20px 60px rgba(0, 0, 0, 0.35), 0 0 0 1px var(--border-subtle)',
      shadowGlowSienna: '0 0 40px rgba(212, 196, 142, 0.08)',
      textureOverlay: "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E\")",
      panelTexture: "url('/textures/linen-weave-dark.svg')",
      success: '#7A9E82',
      successBg: 'rgba(122, 158, 130, 0.14)',
      warning: 'var(--calm-night-warm)',
      warningBg: 'var(--calm-night-warm-muted)',
      danger: '#B08078',
      dangerBg: 'rgba(176, 128, 120, 0.14)',
      info: 'var(--calm-night-accent)',
      infoBg: 'rgba(90, 154, 175, 0.12)',
      sidebarBg: 'rgba(18, 26, 28, 0.94)',
      sidebarActive: 'rgba(212, 196, 142, 0.1)',
      sidebarActiveIndicator: 'var(--calm-night-warm)',
      chartSienna: '#5A9AAF',
      chartBush: '#243238',
      chartOak: '#D4C48E',
      chartCashmere: '#E2E8DC',
      chartSiennaAlpha: 'rgba(90, 154, 175, 0.18)',
      chartOakAlpha: 'rgba(212, 196, 142, 0.22)',
      bodyGradient1: 'radial-gradient(ellipse 75% 55% at 18% 12%, rgba(212, 196, 142, 0.09) 0%, transparent 58%)',
      bodyGradient2: 'radial-gradient(ellipse 60% 50% at 82% 88%, rgba(90, 154, 175, 0.1) 0%, transparent 55%)'
    },
    light: {
      bgBase: '#EBE6DC',
      bgElevated: '#E8E3DA',
      bgSurface: '#E4DFD6',
      bgSurfaceHover: '#E0DBD2',
      bgCard: '#EEE9E1',
      bgCardHover: '#EAE5DD',
      bgGlass: 'rgba(238, 233, 225, 0.88)',
      bgInput: '#E8E3DA',
      textPrimary: '#3A362F',
      textSecondary: 'rgba(58, 54, 47, 0.72)',
      textMuted: 'rgba(58, 54, 47, 0.48)',
      textInverse: '#EEE9E1',
      borderSubtle: 'rgba(106, 100, 92, 0.1)',
      borderDefault: 'rgba(106, 100, 92, 0.16)',
      borderStrong: 'rgba(106, 100, 92, 0.24)',
      borderFocus: 'var(--calm-stone-500)',
      accentPrimary: 'var(--calm-bush)',
      accentPrimaryHover: 'var(--calm-bush-light)',
      accentSecondary: 'var(--calm-cashmere)',
      accentSienna: 'var(--calm-stone-500)',
      shadowXs: '0 1px 2px rgba(58, 54, 47, 0.04)',
      shadowSm: '0 2px 10px rgba(58, 54, 47, 0.06)',
      shadowMd: '0 6px 20px rgba(58, 54, 47, 0.07)',
      shadowLg: '0 12px 36px rgba(58, 54, 47, 0.08)',
      shadowFloat: '0 16px 48px rgba(58, 54, 47, 0.08), 0 0 0 1px var(--border-subtle)',
      shadowGlowSienna: '0 0 32px rgba(122, 114, 104, 0.08)',
      textureOverlay: "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.025'/%3E%3C/svg%3E\")",
      success: '#6E8F7A',
      successBg: 'rgba(110, 143, 122, 0.14)',
      warning: '#A89478',
      warningBg: 'rgba(168, 148, 120, 0.14)',
      danger: '#9A7068',
      dangerBg: 'rgba(154, 112, 104, 0.12)',
      info: 'var(--calm-stone-500)',
      infoBg: 'rgba(122, 114, 104, 0.1)',
      sidebarBg: 'rgba(235, 230, 220, 0.94)',
      sidebarActive: 'rgba(224, 219, 210, 0.7)',
      sidebarActiveIndicator: 'var(--calm-stone-500)',
      chartSienna: '#7A7268',
      chartBush: '#524C44',
      chartOak: '#A89E8E',
      chartCashmere: '#EEE9E1',
      chartSiennaAlpha: 'rgba(122, 114, 104, 0.16)',
      chartOakAlpha: 'rgba(168, 158, 142, 0.28)',
      bodyGradient1: 'radial-gradient(ellipse 70% 55% at 12% 8%, rgba(224, 219, 210, 0.5) 0%, transparent 58%)',
      bodyGradient2: 'radial-gradient(ellipse 55% 45% at 88% 92%, rgba(232, 227, 218, 0.35) 0%, transparent 58%)',
      panelTexture: "url('/textures/linen-weave-light.svg')",
    }
  }
};
