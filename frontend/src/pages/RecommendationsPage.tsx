import React, { useState, useEffect } from 'react';
import { AlertTriangle, BookOpen, RefreshCw, Calendar, Search } from 'lucide-react';
import { formatCurrency, formatNumber } from '../utils/formatters';
import { useTopAnomalies, useAnomalyDetails, useScanHistory } from '../hooks/useRecommendations';
import { LoadingState, ErrorState } from '../components/LoadingErrorState';

export default function RecommendationsPage() {
  const [viewMode, setViewMode] = useState<'single' | 'scan'>('single');
  const [anomalyDate, setAnomalyDate] = useState('2025-06-15');
  const [anomalyKpi, setAnomalyKpi] = useState('revenue');
  const [selectedAnomalyProd, setSelectedAnomalyProd] = useState<string | null>(null);
  
  // Scan parameters
  const [lookbackDays, setLookbackDays] = useState<number>(14);

  // Single date anomalies list
  const { 
    data: topAnomalies, 
    isLoading: anomaliesLoading, 
    isError: isAnomaliesError, 
    error: anomaliesError,
    refetch: refetchAnomalies 
  } = useTopAnomalies(anomalyDate, anomalyKpi);

  // Auto-select first product in single date mode
  useEffect(() => {
    if (viewMode === 'single' && topAnomalies?.top_10_critical_products?.length > 0) {
      setSelectedAnomalyProd(topAnomalies.top_10_critical_products[0].product_id);
    }
  }, [topAnomalies, viewMode]);

  // Scan lookback history query
  const {
    data: scanData,
    isLoading: scanLoading,
    isError: isScanError,
    error: scanError,
    refetch: refetchScan
  } = useScanHistory(selectedAnomalyProd, lookbackDays, anomalyKpi, viewMode === 'scan');

  // Auto-select first flagged date in scan mode
  useEffect(() => {
    if (viewMode === 'scan' && scanData?.anomalous_dates?.length > 0) {
      setAnomalyDate(scanData.anomalous_dates[0].date);
    }
  }, [scanData, viewMode]);

  // Anomaly detail query (RCA)
  const { 
    data: anomalyDetails, 
    isLoading: detailsLoading, 
    isError: isDetailsError, 
    error: detailsError,
    refetch: refetchDetails
  } = useAnomalyDetails(selectedAnomalyProd, anomalyDate, anomalyKpi);

  const handleSync = () => {
    if (viewMode === 'single') {
      refetchAnomalies();
    } else {
      refetchScan();
    }
    if (selectedAnomalyProd) {
      refetchDetails();
    }
  };

  return (
    <>
      <div className="header">
        <div>
          <h1>Anomaly Detection & Root Cause</h1>
          <p>Machine-learning driven deviation alerts and attribution</p>
        </div>
        <button onClick={handleSync} className="filter-select" style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
          <RefreshCw size={14} /> Sync
        </button>
      </div>

      <div className="animate-fade-in">
        {/* View Mode Tabs */}
        <div style={{ display: 'flex', gap: '12px', marginBottom: '20px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
          <button 
            className={`tab-btn`}
            onClick={() => { setViewMode('single'); setAnomalyDate('2025-06-15'); }}
            style={{
              padding: '8px 18px',
              borderRadius: '6px',
              border: 'none',
              background: viewMode === 'single' ? 'var(--primary-hover)' : 'transparent',
              color: viewMode === 'single' ? 'white' : 'var(--text-secondary)',
              cursor: 'pointer',
              fontWeight: '600',
              fontSize: '13px',
              transition: 'all 0.2s',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <Calendar size={14} /> Single Date Check
          </button>
          <button 
            className={`tab-btn`}
            onClick={() => { setViewMode('scan'); setSelectedAnomalyProd(selectedAnomalyProd || 'P001'); }}
            style={{
              padding: '8px 18px',
              borderRadius: '6px',
              border: 'none',
              background: viewMode === 'scan' ? 'var(--primary-hover)' : 'transparent',
              color: viewMode === 'scan' ? 'white' : 'var(--text-secondary)',
              cursor: 'pointer',
              fontWeight: '600',
              fontSize: '13px',
              transition: 'all 0.2s',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <Search size={14} /> Scan History (14d/30d)
          </button>
        </div>

        <div className="filter-bar">
          {viewMode === 'single' && (
            <div className="filter-group">
              <label>Target Date</label>
              <input 
                type="date" className="filter-input" value={anomalyDate}
                min="2025-01-15" max="2025-12-31"
                onChange={(e) => setAnomalyDate(e.target.value)}
              />
            </div>
          )}
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

        {viewMode === 'single' ? (
          anomaliesLoading ? (
            <LoadingState message="Scanning products for anomalies — this may take up to a minute..." />
          ) : isAnomaliesError ? (
            <ErrorState message={anomaliesError instanceof Error ? anomaliesError.message : 'Unknown error'} onRetry={() => refetchAnomalies()} />
          ) : (
            <div className="anomalies-container">
              {/* Left Pane: Single Date Anomalies List */}
              <div className="anomalies-list-card">
                <h3 style={{ fontSize: '13px', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '16px' }}>
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
                        item.status === 'Critical' ? 'critical' : 
                        item.status === 'High' ? 'high' : 
                        item.status === 'Medium' ? 'medium' : 'low'
                      }`}>
                        {item.status}
                      </span>
                    </div>
                  ))
                ) : <p style={{ fontSize: '14px', color: 'var(--text-muted)' }}>No products with high anomaly ratings found.</p>}
              </div>

              {/* Right Pane: Root Cause Details */}
              <div className="anomaly-detail-card">
                {detailsLoading ? (
                  <LoadingState message="Executing 15-layer calculations..." />
                ) : isDetailsError ? (
                  <ErrorState message={detailsError instanceof Error ? detailsError.message : 'Failed to analyze root cause'} onRetry={() => refetchDetails()} />
                ) : anomalyDetails ? (
                  <DetailSection kpi={anomalyKpi} details={anomalyDetails} />
                ) : <p style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>Select a product on the left to view detailed root cause analysis.</p>}
              </div>
            </div>
          )
        ) : (
          /* Scan Mode Layout */
          <div className="anomalies-container">
            {/* Left Pane: Scan Settings & Timeline results */}
            <div className="anomalies-list-card">
              <h3 style={{ fontSize: '13px', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '16px' }}>
                Automated Scanning Panel
              </h3>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '20px' }}>
                <div className="filter-group" style={{ margin: 0 }}>
                  <label>Select Product</label>
                  <select 
                    className="filter-select"
                    value={selectedAnomalyProd || ''}
                    onChange={(e) => setSelectedAnomalyProd(e.target.value)}
                  >
                    <option value="P001">Product P001</option>
                    <option value="P002">Product P002</option>
                    <option value="P003">Product P003</option>
                    <option value="P004">Product P004</option>
                    <option value="P005">Product P005</option>
                  </select>
                </div>
                
                <div className="filter-group" style={{ margin: 0 }}>
                  <label>Scan Window</label>
                  <select 
                    className="filter-select"
                    value={lookbackDays}
                    onChange={(e) => setLookbackDays(Number(e.target.value))}
                  >
                    <option value={14}>Last 14 Days</option>
                    <option value={30}>Last 30 Days</option>
                  </select>
                </div>
              </div>

              <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '16px' }}>
                <h4 style={{ fontSize: '12px', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '12px' }}>
                  Anomalies Flagged ({scanData?.anomalous_dates?.length || 0})
                </h4>
                
                {scanLoading ? (
                  <LoadingState message="Scanning historical timeline..." />
                ) : isScanError ? (
                  <p style={{ color: 'var(--danger)', fontSize: '13px' }}>Error running scan: {scanError instanceof Error ? scanError.message : 'Unknown error'}</p>
                ) : scanData?.anomalous_dates?.length > 0 ? (
                  scanData.anomalous_dates.map((item: any) => (
                    <div 
                      key={item.date}
                      className={`anomaly-item ${anomalyDate === item.date ? 'selected' : ''}`}
                      onClick={() => setAnomalyDate(item.date)}
                      style={{ cursor: 'pointer', marginBottom: '8px' }}
                    >
                      <div>
                        <p style={{ fontWeight: '600', fontSize: '13px' }}>{item.date}</p>
                        <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
                          Var: {item.percentage_change > 0 ? '+' : ''}{item.percentage_change.toFixed(1)}% | Score: {item.severity_score.toFixed(0)}
                        </p>
                      </div>
                      <span className={`severity-tag ${
                        item.status === 'Critical' ? 'critical' : 
                        item.status === 'High' ? 'high' : 
                        item.status === 'Medium' ? 'medium' : 'low'
                      }`}>
                        {item.status}
                      </span>
                    </div>
                  ))
                ) : (
                  <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>No anomalies detected in the selected lookback range.</p>
                )}
              </div>
            </div>

            {/* Right Pane: Detailed Root Cause for the selected date */}
            <div className="anomaly-detail-card">
              {detailsLoading ? (
                <LoadingState message="Running 15-layer attribution diagnostics..." />
              ) : isDetailsError ? (
                <ErrorState message={detailsError instanceof Error ? detailsError.message : 'Failed to analyze root cause'} onRetry={() => refetchDetails()} />
              ) : anomalyDetails ? (
                <DetailSection kpi={anomalyKpi} details={anomalyDetails} />
              ) : <p style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>Select an anomalous date on the left to inspect root causes.</p>}
            </div>
          </div>
        )}
      </div>
    </>
  );
}

// Subcomponent to render details of an anomaly
function DetailSection({ kpi, details }: { kpi: string, details: any }) {
  return (
    <div className="animate-fade-in">
      <div className="anomaly-detail-header">
        <div>
          <h2 style={{ margin: '0' }}>Product {details.product_id} Diagnostic Report</h2>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '4px' }}>
            KPI Checked: {details.kpi} | Date: {details.target_date}
          </p>
        </div>
        <span className={`severity-tag ${
          details.status === 'Critical' ? 'critical pulse-critical' : 
          details.status === 'High' ? 'high pulse-high' : 
          details.status === 'Medium' ? 'medium' : 'low'
        }`}>
          {details.status} ({details.severity_score.toFixed(0)}/100)
        </span>
      </div>

      <div className="anomaly-metric-comparison">
        <div>
          <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Expected Baseline</label>
          <p style={{ fontSize: '18px', fontWeight: '700', margin: '4px 0 0 0' }}>
            {kpi === 'revenue' || kpi === 'profit' ? formatCurrency(details.expected_value) : 
             kpi === 'conversion_rate' || kpi === 'retention_rate' ? `${(details.expected_value * 100).toFixed(2)}%` : 
             formatNumber(details.expected_value.toFixed(0))}
          </p>
        </div>
        <div>
          <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Actual Value</label>
          <p style={{ fontSize: '18px', fontWeight: '700', margin: '4px 0 0 0', color: details.percentage_change < 0 ? 'var(--danger)' : 'var(--success)' }}>
            {kpi === 'revenue' || kpi === 'profit' ? formatCurrency(details.actual_value) : 
             kpi === 'conversion_rate' || kpi === 'retention_rate' ? `${(details.actual_value * 100).toFixed(2)}%` : 
             formatNumber(details.actual_value.toFixed(0))}
          </p>
        </div>
        <div>
          <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Variance (Error %)</label>
          <p style={{ fontSize: '18px', fontWeight: '700', margin: '4px 0 0 0', color: details.percentage_change < 0 ? 'var(--danger)' : 'var(--success)' }}>
            {details.percentage_change > 0 ? '+' : ''}{details.percentage_change}%
          </p>
        </div>
      </div>

      {details.explanation?.top_drivers?.length > 0 && (
        <div className="detail-section">
          <h4>
            <BookOpen size={14} style={{ marginRight: '6px', color: 'var(--primary-hover)', verticalAlign: 'middle' }} /> 
            Attributed Outlier Drivers (RCA via SHAP)
          </h4>
          <div className="driver-bar-container">
            {details.explanation.top_drivers.map((drv: any, idx: number) => {
              const maxVal = Math.max(...details.explanation.top_drivers.map((d: any) => Math.abs(d.shap_value)));
              const pct = maxVal > 0 ? (Math.abs(drv.shap_value) / maxVal) * 100 : 0;
              const isNegative = drv.shap_value < 0;
              return (
                <div key={idx} className="driver-row">
                  <span className="driver-name" title={drv.feature}>{drv.feature}</span>
                  <div className="driver-bar-wrapper">
                    <div 
                      className={`driver-bar ${isNegative ? 'negative' : 'positive'}`}
                      style={{ width: `${pct}%`, float: isNegative ? 'right' : 'left' }}
                    />
                  </div>
                  <span className="driver-val" style={{ color: isNegative ? 'var(--danger)' : 'var(--success)' }}>
                    {drv.shap_value > 0 ? '+' : ''}{drv.shap_value.toFixed(2)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
