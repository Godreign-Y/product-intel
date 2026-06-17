import React, { useState, useEffect } from 'react';
import { AlertTriangle, BookOpen, RefreshCw } from 'lucide-react';
import { formatCurrency, formatNumber } from '../utils/formatters';
import { useTopAnomalies, useAnomalyDetails } from '../hooks/useRecommendations';
import { LoadingState, ErrorState } from '../components/LoadingErrorState';

export default function RecommendationsPage() {
  const [anomalyDate, setAnomalyDate] = useState('2025-06-15');
  const [anomalyKpi, setAnomalyKpi] = useState('revenue');
  const [selectedAnomalyProd, setSelectedAnomalyProd] = useState<string | null>(null);

  const { 
    data: topAnomalies, 
    isLoading: anomaliesLoading, 
    isError: isAnomaliesError, 
    error: anomaliesError,
    refetch: refetchAnomalies 
  } = useTopAnomalies(anomalyDate, anomalyKpi);

  useEffect(() => {
    if (topAnomalies?.top_10_critical_products?.length > 0) {
      setSelectedAnomalyProd(topAnomalies.top_10_critical_products[0].product_id);
    }
  }, [topAnomalies]);

  const { 
    data: anomalyDetails, 
    isLoading: detailsLoading, 
    isError: isDetailsError, 
    error: detailsError,
    refetch: refetchDetails
  } = useAnomalyDetails(selectedAnomalyProd, anomalyDate, anomalyKpi);

  return (
    <>
      <div className="header">
        <div>
          <h1>Anomaly Detection & Root Cause</h1>
          <p>Machine-learning driven deviation alerts and attribution</p>
        </div>
        <button onClick={() => { refetchAnomalies(); if (selectedAnomalyProd) refetchDetails(); }} className="filter-select" style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
          <RefreshCw size={14} /> Sync
        </button>
      </div>

      <div className="animate-fade-in">
        <div className="filter-bar">
          <div className="filter-group">
            <label>Target Date</label>
            <input 
              type="date" className="filter-input" value={anomalyDate}
              min="2025-01-15" max="2025-12-31"
              onChange={(e) => setAnomalyDate(e.target.value)}
            />
          </div>
          <div className="filter-group">
            <label>Target KPI</label>
            <select 
              className="filter-select" value={anomalyKpi}
              onChange={(e) => setAnomalyKpi(e.target.value)}
            >
              <option value="revenue">Revenue</option>
              <option value="profit">Profit</option>
              <option value="orders">Orders</option>
              <option value="conversion_rate">Conversion Rate</option>
              <option value="retention_rate">Retention Rate</option>
            </select>
          </div>
        </div>

        {anomaliesLoading ? (
          <LoadingState message="Scanning products for anomalies — this may take up to a minute..." />
        ) : isAnomaliesError ? (
          <ErrorState message={anomaliesError instanceof Error ? anomaliesError.message : 'Unknown error'} onRetry={() => refetchAnomalies()} />
        ) : (
          <div className="anomalies-container">
            <div className="anomalies-list-card">
              <h3 style={{ fontSize: '15px', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '16px' }}>
                Ranked Risk Products ({anomalyDate})
              </h3>
              
              {topAnomalies?.top_10_critical_products?.length > 0 ? (
                topAnomalies.top_10_critical_products.map((item: any) => (
                  <div 
                    key={item.product_id}
                    className={`anomaly-item ${selectedAnomalyProd === item.product_id ? 'selected' : ''}`}
                    onClick={() => setSelectedAnomalyProd(item.product_id)}
                  >
                    <div>
                      <p style={{ fontWeight: '600', fontSize: '14px' }}>Product {item.product_id}</p>
                      <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                        Score: {item.severity_score.toFixed(0)}/100
                      </p>
                    </div>
                    <span className={`severity-tag ${
                      item.severity_status === 'Critical' ? 'critical' : 
                      item.severity_status === 'High' ? 'high' : 
                      item.severity_status === 'Medium' ? 'medium' : 'low'
                    }`}>
                      {item.severity_status}
                    </span>
                  </div>
                ))
              ) : <p style={{ fontSize: '14px', color: 'var(--text-muted)' }}>No products with high anomaly ratings found.</p>}
            </div>

            <div className="anomaly-detail-card">
              {detailsLoading ? (
                <LoadingState message="Executing 15-layer calculations..." />
              ) : isDetailsError ? (
                <ErrorState message={detailsError instanceof Error ? detailsError.message : 'Failed to analyze root cause'} onRetry={() => refetchDetails()} />
              ) : anomalyDetails ? (
                <div className="animate-fade-in">
                  <div className="anomaly-detail-header">
                    <div>
                      <h2 style={{ margin: '0' }}>Product {anomalyDetails.product_id} Anomalies</h2>
                      <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '4px' }}>
                        KPI Checked: {anomalyDetails.kpi} | Date: {anomalyDetails.target_date}
                      </p>
                    </div>
                    <span className={`severity-tag ${
                      anomalyDetails.status === 'Critical' ? 'critical pulse-critical' : 
                      anomalyDetails.status === 'High' ? 'high pulse-high' : 
                      anomalyDetails.status === 'Medium' ? 'medium' : 'low'
                    }`}>
                      {anomalyDetails.status} ({anomalyDetails.severity_score.toFixed(0)}/100)
                    </span>
                  </div>

                  <div className="anomaly-metric-comparison">
                    <div>
                      <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Expected Baseline</label>
                      <p style={{ fontSize: '18px', fontWeight: '700', margin: '4px 0 0 0' }}>
                        {anomalyKpi === 'revenue' || anomalyKpi === 'profit' ? formatCurrency(anomalyDetails.expected_value) : 
                         anomalyKpi === 'conversion_rate' || anomalyKpi === 'retention_rate' ? `${(anomalyDetails.expected_value * 100).toFixed(2)}%` : 
                         formatNumber(anomalyDetails.expected_value.toFixed(0))}
                      </p>
                    </div>
                    <div>
                      <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Actual Value</label>
                      <p style={{ fontSize: '18px', fontWeight: '700', margin: '4px 0 0 0', color: anomalyDetails.percentage_change < 0 ? 'var(--danger)' : 'var(--success)' }}>
                        {anomalyKpi === 'revenue' || anomalyKpi === 'profit' ? formatCurrency(anomalyDetails.actual_value) : 
                         anomalyKpi === 'conversion_rate' || anomalyKpi === 'retention_rate' ? `${(anomalyDetails.actual_value * 100).toFixed(2)}%` : 
                         formatNumber(anomalyDetails.actual_value.toFixed(0))}
                      </p>
                    </div>
                    <div>
                      <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Variance (Error %)</label>
                      <p style={{ fontSize: '18px', fontWeight: '700', margin: '4px 0 0 0', color: anomalyDetails.percentage_change < 0 ? 'var(--danger)' : 'var(--success)' }}>
                        {anomalyDetails.percentage_change > 0 ? '+' : ''}{anomalyDetails.percentage_change}%
                      </p>
                    </div>
                  </div>

                  {anomalyDetails.explanation?.top_drivers?.length > 0 && (
                    <div className="detail-section">
                      <h4><BookOpen size={14} style={{ marginRight: '6px', color: 'var(--primary-hover)', verticalAlign: 'middle' }} /> Attributed Outlier Drivers (RCA)</h4>
                      <div className="driver-bar-container">
                        {anomalyDetails.explanation.top_drivers.map((drv: any, idx: number) => {
                          const maxVal = Math.max(...anomalyDetails.explanation.top_drivers.map((d: any) => Math.abs(d.shap_value)));
                          const pct = maxVal > 0 ? (Math.abs(drv.shap_value) / maxVal) * 100 : 0;
                          return (
                            <div key={idx} className="driver-row">
                              <span className="driver-name" title={drv.clean_name}>{drv.clean_name}</span>
                              <div className="driver-bar-wrapper">
                                <div 
                                  className={`driver-bar ${drv.impact_direction === 'negative' ? 'negative' : 'positive'}`}
                                  style={{ width: `${pct}%`, float: drv.impact_direction === 'negative' ? 'right' : 'left' }}
                                />
                              </div>
                              <span className="driver-val" style={{ color: drv.impact_direction === 'negative' ? 'var(--danger)' : 'var(--success)' }}>
                                {drv.impact_direction === 'negative' ? '' : '+'}{drv.shap_value.toFixed(2)}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                </div>
              ) : <p style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>Select a product on the left to view detailed root cause analysis.</p>}
            </div>
          </div>
        )}
      </div>
    </>
  );
}
