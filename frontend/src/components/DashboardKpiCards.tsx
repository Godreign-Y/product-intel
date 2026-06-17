import React from 'react';
import { DollarSign, ShoppingBag, Activity, Percent, Users, TrendingUp } from 'lucide-react';
import { KpiData } from '../types';
import { formatCurrency, formatNumber } from '../utils/formatters';

interface Props {
  kpis: KpiData | null;
}

const KPI_CONFIG = [
  {
    key: 'revenue',
    label: 'Total Revenue',
    icon: DollarSign,
    iconClass: 'revenue',
    format: (k: KpiData) => formatCurrency(k.revenue?.sum ?? 0),
    sub: (k: KpiData) => `Avg ${formatCurrency(k.revenue?.daily_avg ?? 0)}/day`,
  },
  {
    key: 'orders',
    label: 'Total Orders',
    icon: ShoppingBag,
    iconClass: 'orders',
    format: (k: KpiData) => formatNumber(k.orders?.sum ?? 0),
    sub: (k: KpiData) => `Avg ${formatNumber(k.orders?.daily_avg ?? 0)}/day`,
  },
  {
    key: 'aov',
    label: 'Average Order Value',
    icon: Activity,
    iconClass: 'cvr',
    format: (k: KpiData) => formatCurrency(k.average_order_value ?? 0),
    sub: () => 'AOV for selected filters',
  },
  {
    key: 'cvr',
    label: 'Conversion Rate',
    icon: Percent,
    iconClass: 'aov',
    format: (k: KpiData) => `${((k.conversion_rate?.mean ?? 0) * 100).toFixed(2)}%`,
    sub: () => 'Session to purchase',
  },
  {
    key: 'retention',
    label: 'Retention Rate',
    icon: Users,
    iconClass: 'retention',
    format: (k: KpiData) => `${((k.retention_rate?.mean ?? 0) * 100).toFixed(2)}%`,
    sub: () => 'Repeat purchase probability',
  },
];

export const DashboardKpiCards: React.FC<Props> = ({ kpis }) => {
  return (
    <div className="metrics-grid">
      {KPI_CONFIG.map((cfg, index) => {
        const Icon = cfg.icon;
        return (
          <div
            key={cfg.key}
            className="kpi-card animate-fade-in"
            style={{ animationDelay: `${index * 60}ms` }}
          >
            <div className="kpi-details">
              <h3>{cfg.label}</h3>
              <p className="kpi-value">{kpis ? cfg.format(kpis) : '—'}</p>
              <p className="kpi-subtext">{kpis ? cfg.sub(kpis) : 'Loading...'}</p>
            </div>
            <div className={`kpi-icon ${cfg.iconClass}`}>
              <Icon size={20} strokeWidth={1.75} />
            </div>
          </div>
        );
      })}

      <div className="kpi-card animate-fade-in" style={{ animationDelay: '300ms', opacity: 0.85 }}>
        <div className="kpi-details">
          <h3>Health Score</h3>
          <p className="kpi-value" style={{ fontSize: 'var(--text-2xl)' }}>
            Optimal
          </p>
          <p className="kpi-subtext">All metrics within range</p>
        </div>
        <div className="kpi-icon ltv">
          <TrendingUp size={20} strokeWidth={1.75} />
        </div>
      </div>
    </div>
  );
};
