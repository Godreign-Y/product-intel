/**
 * Calm Design System — ProductIntel
 *
 * Color Tokens:
 *   --calm-sienna    #A55A32  Primary accent
 *   --calm-cashmere  #E7DED2  Background surface
 *   --calm-oak       #CDB08D  Secondary surface
 *   --calm-bush      #0B2420  Dark accent
 *   --calm-charcoal  #2D3237  Charcoal background
 *
 * Typography:
 *   Typeface: IBM Plex Sans (single-family hierarchy)
 *
 * Spacing: --space-1 (4px) through --space-24 (96px)
 * Radius:  --radius-sm (10px) through --radius-xl (24px)
 * Motion:  --transition-base (300ms)
 */

export { Button } from '../components/ui/Button';
export { Card, CardHeader } from '../components/ui/Card';
export { Badge, Toggle } from '../components/ui/Badge';
export { Table } from '../components/ui/Table';
export type { Column } from '../components/ui/Table';
export { Skeleton, DashboardSkeleton, TableSkeleton } from '../components/ui/Skeleton';
export { CHART_COLORS, getChartScales, getChartLegend } from '../utils/chartTheme';
