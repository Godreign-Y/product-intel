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
    label: 'Revenue',
    icon: DollarSign,
    format: (k: KpiData) => formatCurrency(k.revenue?.sum ?? 0),
    sub: (k: KpiData) => `${formatCurrency(k.revenue?.daily_avg ?? 0)} daily avg`,
  },
  {
    key: 'orders',
    label: 'Orders',
    icon: ShoppingBag,
    format: (k: KpiData) => formatNumber(k.orders?.sum ?? 0),
    sub: (k: KpiData) => `${formatNumber(k.orders?.daily_avg ?? 0)} per day`,
  },
  {
    key: 'aov',
    label: 'Order value',
    icon: Activity,
    format: (k: KpiData) => formatCurrency(k.average_order_value ?? 0),
    sub: () => 'Average basket size',
  },
  {
    key: 'cvr',
    label: 'Conversion',
    icon: Percent,
    format: (k: KpiData) => `${((k.conversion_rate?.mean ?? 0) * 100).toFixed(2)}%`,
    sub: () => 'Sessions that buy',
  },
  {
    key: 'retention',
    label: 'Retention',
    icon: Users,
    format: (k: KpiData) => `${((k.retention_rate?.mean ?? 0) * 100).toFixed(2)}%`,
    sub: () => 'Customers who return',
  },
];

export const DashboardKpiCards: React.FC<Props> = ({ kpis }) => {
  return (
    <div className="pin-masonry-kpis">
      {KPI_CONFIG.map((cfg, index) => {
        const Icon = cfg.icon;
        return (
          <div
            key={cfg.key}
            className="pin-kpi animate-fade-in"
            style={{ animationDelay: `${index * 70}ms` }}
          >
            <div className="pin-kpi-top">
              <span className="pin-kpi-label">{cfg.label}</span>
              <div className="pin-kpi-icon">
                <Icon size={18} strokeWidth={1.75} />
              </div>
            </div>
            <p className="pin-kpi-value">{kpis ? cfg.format(kpis) : '—'}</p>
            <p className="pin-kpi-sub">{kpis ? cfg.sub(kpis) : 'Loading…'}</p>
          </div>
        );
      })}

      <div className="pin-kpi animate-fade-in" style={{ animationDelay: '350ms' }}>
        <div className="pin-kpi-top">
          <span className="pin-kpi-label">Health</span>
          <div className="pin-kpi-icon">
            <TrendingUp size={18} strokeWidth={1.75} />
          </div>
        </div>
        <p className="pin-kpi-value">Optimal</p>
        <p className="pin-kpi-sub">All metrics in range</p>
      </div>
    </div>
  );
};
