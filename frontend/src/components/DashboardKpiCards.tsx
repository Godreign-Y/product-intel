import React from 'react';
import { DollarSign, ShoppingBag, Activity, Percent, Users } from 'lucide-react';
import { KpiData } from '../types';
import { formatCurrency, formatNumber } from '../utils/formatters';

interface Props {
  kpis: KpiData | null;
}

export const DashboardKpiCards: React.FC<Props> = ({ kpis }) => {
  return (
    <div className="metrics-grid">
      <div className="kpi-card">
        <div className="kpi-details">
          <h3>Total Revenue</h3>
          <p className="kpi-value">{kpis?.revenue ? formatCurrency(kpis.revenue.sum) : '$0'}</p>
          <p className="kpi-subtext">Avg {kpis?.revenue ? formatCurrency(kpis.revenue.daily_avg) : '$0'}/day</p>
        </div>
        <div className="kpi-icon revenue">
          <DollarSign size={20} />
        </div>
      </div>

      <div className="kpi-card">
        <div className="kpi-details">
          <h3>Total Orders</h3>
          <p className="kpi-value">{kpis?.orders ? formatNumber(kpis.orders.sum) : '0'}</p>
          <p className="kpi-subtext">Avg {kpis?.orders ? formatNumber(kpis.orders.daily_avg) : '0'}/day</p>
        </div>
        <div className="kpi-icon orders">
          <ShoppingBag size={20} />
        </div>
      </div>

      <div className="kpi-card">
        <div className="kpi-details">
          <h3>Average Order Value</h3>
          <p className="kpi-value">{kpis?.average_order_value ? formatCurrency(kpis.average_order_value) : '$0.00'}</p>
          <p className="kpi-subtext">AOV for select filters</p>
        </div>
        <div className="kpi-icon cvr">
          <Activity size={20} />
        </div>
      </div>

      <div className="kpi-card">
        <div className="kpi-details">
          <h3>Conversion Rate</h3>
          <p className="kpi-value">{kpis?.conversion_rate ? `${(kpis.conversion_rate.mean * 100).toFixed(2)}%` : '0.00%'}</p>
          <p className="kpi-subtext">Session to purchase</p>
        </div>
        <div className="kpi-icon aov">
          <Percent size={20} />
        </div>
      </div>

      <div className="kpi-card">
        <div className="kpi-details">
          <h3>Retention Rate</h3>
          <p className="kpi-value">{kpis?.retention_rate ? `${(kpis.retention_rate.mean * 100).toFixed(2)}%` : '0.00%'}</p>
          <p className="kpi-subtext">Repeat purchase probability</p>
        </div>
        <div className="kpi-icon retention">
          <Users size={20} />
        </div>
      </div>
    </div>
  );
};
