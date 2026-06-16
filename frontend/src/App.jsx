import React, { useState, useEffect, useRef } from 'react';
import 'chart.js/auto';
import { Line, Doughnut, Bar } from 'react-chartjs-2';
import { 
  LayoutDashboard, 
  TrendingUp, 
  AlertTriangle, 
  MessageSquare, 
  Calendar, 
  DollarSign, 
  ShoppingBag, 
  Users, 
  Percent, 
  Activity, 
  Package, 
  ChevronRight, 
  ArrowUpRight, 
  ArrowDownRight, 
  Sparkles, 
  RefreshCw,
  Search,
  BookOpen
} from 'lucide-react';
import './App.css';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedProduct, setSelectedProduct] = useState('P001');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [startDate, setStartDate] = useState('2025-01-01');
  const [endDate, setEndDate] = useState('2025-12-31');
  
  // Dashboard states
  const [kpis, setKpis] = useState(null);
  const [channelData, setChannelData] = useState(null);
  const [campaignData, setCampaignData] = useState(null);
  const [inventoryData, setInventoryData] = useState(null);
  const [dashboardLoading, setDashboardLoading] = useState(false);
  
  // Trends states
  const [trendMetric, setTrendMetric] = useState('revenue');
  const [trendGranularity, setTrendGranularity] = useState('daily');
  const [trendData, setTrendData] = useState(null);
  const [trendsLoading, setTrendsLoading] = useState(false);
  
  // Anomalies states
  const [anomalyDate, setAnomalyDate] = useState('2025-12-31');
  const [anomalyKpi, setAnomalyKpi] = useState('revenue');
  const [anomalyReport, setAnomalyReport] = useState(null);
  const [selectedAnomalyProd, setSelectedAnomalyProd] = useState(null);
  const [anomalyDetails, setAnomalyDetails] = useState(null);
  const [anomaliesLoading, setAnomaliesLoading] = useState(false);
  const [anomalyDetailsLoading, setAnomalyDetailsLoading] = useState(false);
  
  // Chat states
  const [chatInput, setChatInput] = useState('');
  const [messages, setMessages] = useState([
    {
      sender: 'assistant',
      text: 'Hello! I am your AI-powered Business Intelligence Assistant. Ask me anything about product performance, revenue drivers, declining trends, scenario simulations, or anomaly explanations!'
    }
  ]);
  const [chatLoading, setChatLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Products list P001 - P100
  const products = Array.from({ length: 100 }, (_, i) => `P${String(i + 1).padStart(3, '0')}`);

  // Intelligence Repository states
  const [repoTab, setRepoTab] = useState('reports'); // 'reports', 'experiments', 'search', 'insights'
  const [reports, setReports] = useState([]);
  const [experiments, setExperiments] = useState([]);
  const [selectedExperimentId, setSelectedExperimentId] = useState(null);
  const [selectedItemDetail, setSelectedItemDetail] = useState(null);
  const [repoLoading, setRepoLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  
  // Search / Insights states
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [searchLoading, setSearchLoading] = useState(false);
  
  const [insightsTopic, setInsightsTopic] = useState('pricing');
  const [insightsResult, setInsightsResult] = useState(null);
  const [insightsLoading, setInsightsLoading] = useState(false);

  useEffect(() => {
    fetchDashboardData();
  }, [selectedProduct, selectedCategory, startDate, endDate]);

  useEffect(() => {
    if (activeTab === 'repository') {
      fetchRepoData();
      handleExtractInsights('pricing');
    }
  }, [activeTab]);

  const fetchRepoData = async () => {
    setRepoLoading(true);
    try {
      // Fetch Experiments (and reports)
      const expsRes = await fetch('/api/v1/history/experiments?limit=50');
      const expsData = await expsRes.json();
      setExperiments(expsData);
      setReports(expsData); // Using the list as basic explorer
      
      // Auto select first experiment
      if (expsData.length > 0) {
        setSelectedExperimentId(expsData[0].id);
        fetchReportDetails(expsData[0].id);
      }
    } catch (e) {
      console.error("Failed to fetch repository data", e);
    } finally {
      setRepoLoading(false);
    }
  };

  const fetchReportDetails = async (experimentId) => {
    setDetailLoading(true);
    try {
      const res = await fetch(`/api/v1/history/reports/${experimentId}`);
      const data = await res.json();
      setSelectedItemDetail(data);
    } catch (e) {
      console.error("Failed to fetch report details", e);
      setSelectedItemDetail(null);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleRepoSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setSearchLoading(true);
    try {
      const res = await fetch('/api/v1/history/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery, limit: 5 })
      });
      const data = await res.json();
      setSearchResults(data);
    } catch (e) {
      console.error("Semantic search failed", e);
    } finally {
      setSearchLoading(false);
    }
  };

  const handleExtractInsights = async (topic) => {
    setInsightsLoading(true);
    try {
      const res = await fetch(`/api/v1/history/insights?topic=${topic}`);
      const data = await res.json();
      setInsightsResult(data);
    } catch (e) {
      console.error("Failed to extract insights", e);
    } finally {
      setInsightsLoading(false);
    }
  };

  useEffect(() => {
    fetchTrendData();
  }, [selectedProduct, trendMetric, trendGranularity, startDate, endDate]);

  useEffect(() => {
    fetchAnomalies();
  }, [anomalyDate, anomalyKpi]);

  useEffect(() => {
    if (selectedAnomalyProd) {
      fetchAnomalyDetails(selectedAnomalyProd);
    }
  }, [selectedAnomalyProd, anomalyDate, anomalyKpi]);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const fetchDashboardData = async () => {
    setDashboardLoading(true);
    try {
      const payload = {
        start_date: startDate || null,
        end_date: endDate || null,
        product_id: selectedProduct || null,
        category: selectedCategory || null
      };

      // Fetch KPIs
      const kpiRes = await fetch('/api/v1/analytics/kpi', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const kpiData = await kpiRes.json();
      setKpis(kpiData);

      // Fetch Channel Mix
      const channelRes = await fetch('/api/v1/analytics/channel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const chanData = await channelRes.json();
      setChannelData(chanData);

      // Fetch Campaign Mix
      const campaignRes = await fetch('/api/v1/analytics/campaign', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const campData = await campaignRes.json();
      setCampaignData(campData);

      // Fetch Inventory (only makes sense for single product filter)
      if (selectedProduct) {
        const invRes = await fetch('/api/v1/analytics/inventory', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            product_id: selectedProduct,
            start_date: startDate || null,
            end_date: endDate || null
          })
        });
        const invData = await invRes.json();
        setInventoryData(invData);
      } else {
        setInventoryData(null);
      }

    } catch (e) {
      console.error("Failed to fetch dashboard data", e);
    } finally {
      setDashboardLoading(false);
    }
  };

  const fetchTrendData = async () => {
    setTrendsLoading(true);
    try {
      const payload = {
        metric: trendMetric,
        start_date: startDate || null,
        end_date: endDate || null,
        product_id: selectedProduct || null,
        granularity: trendGranularity
      };

      const res = await fetch('/api/v1/analytics/trend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      setTrendData(data);
    } catch (e) {
      console.error("Failed to fetch trends", e);
    } finally {
      setTrendsLoading(false);
    }
  };

  const fetchAnomalies = async () => {
    setAnomaliesLoading(true);
    try {
      const payload = {
        target_date: anomalyDate,
        kpi: anomalyKpi
      };

      const res = await fetch('/api/v1/anomaly/top-products', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      setAnomalyReport(data);
      
      // Auto select first critical product if available
      if (data?.top_10_critical_products?.length > 0) {
        setSelectedAnomalyProd(data.top_10_critical_products[0].product_id);
      } else {
        setSelectedAnomalyProd(null);
        setAnomalyDetails(null);
      }
    } catch (e) {
      console.error("Failed to fetch anomalies list", e);
    } finally {
      setAnomaliesLoading(false);
    }
  };

  const fetchAnomalyDetails = async (prodId) => {
    setAnomalyDetailsLoading(true);
    try {
      const payload = {
        product_id: prodId,
        target_date: anomalyDate,
        kpi: anomalyKpi
      };

      const res = await fetch('/api/v1/anomaly/detect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      setAnomalyDetails(data);
    } catch (e) {
      console.error("Failed to fetch anomaly details", e);
    } finally {
      setAnomalyDetailsLoading(false);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!chatInput.trim() || chatLoading) return;

    const userQuery = chatInput;
    setMessages(prev => [...prev, { sender: 'user', text: userQuery }]);
    setChatInput('');
    setChatLoading(true);

    try {
      const res = await fetch('/api/v1/agent/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userQuery })
      });
      const data = await res.json();
      setMessages(prev => [...prev, { 
        sender: 'assistant', 
        text: data.response,
        meta: {
          route: data.route_called,
          raw: data.raw_data
        }
      }]);
    } catch (err) {
      setMessages(prev => [...prev, { 
        sender: 'assistant', 
        text: 'Sorry, I encountered an error while communicating with the analytics model: ' + err.message 
      }]);
    } finally {
      setChatLoading(false);
    }
  };

  // Format helper for currency
  const formatCurrency = (val) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val);
  };

  // Format helper for large numbers
  const formatNumber = (val) => {
    return new Intl.NumberFormat('en-US').format(val);
  };

  // Convert markdown-like headers and tables in AI text to basic HTML elements
  const renderMarkdown = (text) => {
    if (!text) return '';
    let processed = text
      .replace(/### (.*)/g, '<h4>$1</h4>')
      .replace(/## (.*)/g, '<h3>$1</h3>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`([^`]+)`/g, '<code>$1</code>');
      
    // Handle list items
    processed = processed.replace(/^\s*[\*\-]\s+(.*)/gm, '<li>$1</li>');
    
    // Wrap consecutive list items
    const lines = processed.split('\n');
    let inList = false;
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].startsWith('<li>') && !inList) {
        lines[i] = '<ul>' + lines[i];
        inList = true;
      } else if (!lines[i].startsWith('<li>') && inList) {
        lines[i - 1] = lines[i - 1] + '</ul>';
        inList = false;
      }
    }
    if (inList) lines[lines.length - 1] = lines[lines.length - 1] + '</ul>';
    
    // Parse tables
    let inTable = false;
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].startsWith('|') && lines[i].endsWith('|')) {
        const cells = lines[i].split('|').map(c => c.trim()).filter(c => c !== '');
        
        // Check if header line or separator
        if (lines[i].includes('---')) {
          lines[i] = ''; // skip separator
          continue;
        }
        
        const isHeader = i > 0 && lines[i-1].includes('---') || i === 0 && lines[i+1]?.includes('---');
        const cellTag = isHeader ? 'th' : 'td';
        
        let rowContent = `<tr>${cells.map(c => `<${cellTag}>${c}</${cellTag}>`).join('')}</tr>`;
        
        if (!inTable) {
          rowContent = `<table><thead>${rowContent}</thead><tbody>`;
          inTable = true;
        }
        lines[i] = rowContent;
      } else if (inTable) {
        lines[i-1] = lines[i-1] + '</tbody></table>';
        inTable = false;
      }
    }
    
    return lines.join('\n');
  };

  // Charts Configs
  const trendChartConfig = trendData?.history ? {
    labels: trendData.history.map(pt => pt.date),
    datasets: [{
      label: `${trendMetric.toUpperCase()} (${trendGranularity})`,
      data: trendData.history.map(pt => pt.value),
      borderColor: '#8b5cf6',
      backgroundColor: 'rgba(139, 92, 246, 0.15)',
      fill: true,
      tension: 0.3,
      borderWidth: 2,
      pointRadius: trendGranularity === 'daily' ? 0 : 4,
      pointHoverRadius: 6
    }]
  } : null;

  const channelChartConfig = channelData?.channel_mix ? {
    labels: Object.keys(channelData.channel_mix),
    datasets: [{
      data: Object.values(channelData.channel_mix).map(v => v * 100),
      backgroundColor: ['#8b5cf6', '#10b981', '#06b6d4', '#f59e0b'],
      borderWidth: 0,
      hoverOffset: 4
    }]
  } : null;

  const campaignChartConfig = campaignData?.campaign_mix ? {
    labels: Object.keys(campaignData.campaign_mix),
    datasets: [{
      label: 'Campaign Mix Share (%)',
      data: Object.values(campaignData.campaign_mix).map(v => v * 100),
      backgroundColor: ['rgba(139, 92, 246, 0.6)', 'rgba(16, 185, 129, 0.6)', 'rgba(6, 182, 212, 0.6)', 'rgba(245, 158, 11, 0.6)'],
      borderColor: ['#8b5cf6', '#10b981', '#06b6d4', '#f59e0b'],
      borderWidth: 1
    }]
  } : null;

  return (
    <div className="app-container">
      {/* Sidebar */}
      <div className="sidebar">
        <div className="logo-container">
          <Sparkles size={24} className="kpi-icon ltv" />
          <span className="logo-text">ProductIntel</span>
        </div>
        
        <div className="nav-links">
          <button 
            className={`nav-button ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <LayoutDashboard size={18} />
            Dashboard
          </button>
          <button 
            className={`nav-button ${activeTab === 'trends' ? 'active' : ''}`}
            onClick={() => setActiveTab('trends')}
          >
            <TrendingUp size={18} />
            Trend Analysis
          </button>
          <button 
            className={`nav-button ${activeTab === 'anomalies' ? 'active' : ''}`}
            onClick={() => setActiveTab('anomalies')}
          >
            <AlertTriangle size={18} />
            Anomalies
          </button>
          <button 
            className={`nav-button ${activeTab === 'repository' ? 'active' : ''}`}
            onClick={() => setActiveTab('repository')}
          >
            <BookOpen size={18} />
            Repository
          </button>
          <button 
            className={`nav-button ${activeTab === 'assistant' ? 'active' : ''}`}
            onClick={() => setActiveTab('assistant')}
          >
            <MessageSquare size={18} />
            AI Assistant
          </button>
        </div>
      </div>

      {/* Main Panel Content */}
      <div className="main-content">
        
        {/* Title Bar */}
        <div className="header">
          <div>
            <h1>
              {activeTab === 'dashboard' && 'Performance Overview'}
              {activeTab === 'trends' && 'Historical Trends'}
              {activeTab === 'anomalies' && 'Anomaly Detection Engine'}
              {activeTab === 'repository' && 'Historical Intelligence Repository'}
              {activeTab === 'assistant' && 'AI Analytics Assistant'}
            </h1>
            <p>
              {activeTab === 'dashboard' && 'Core business metrics and sales distributions'}
              {activeTab === 'trends' && 'Identify linear regressions and period growth velocities'}
              {activeTab === 'anomalies' && 'Multi-layer statistical outliers and rule violations'}
              {activeTab === 'repository' && 'Automated business memory, statistical A/B tests, and semantic retrieval'}
              {activeTab === 'assistant' && 'Ask natural language queries and simulate what-if scenarios'}
            </p>
          </div>
          
          {/* Refresh Action */}
          <button 
            onClick={() => {
              if (activeTab === 'dashboard') fetchDashboardData();
              else if (activeTab === 'trends') fetchTrendData();
              else if (activeTab === 'anomalies') fetchAnomalies();
              else if (activeTab === 'repository') fetchRepoData();
            }}
            className="filter-select"
            style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}
          >
            <RefreshCw size={14} className={dashboardLoading || trendsLoading || anomaliesLoading || repoLoading ? 'spin' : ''} />
            Sync
          </button>
        </div>

        {/* Global Filter Bar (Dashboard & Trends tabs only) */}
        {(activeTab === 'dashboard' || activeTab === 'trends') && (
          <div className="filter-bar animate-fade-in">
            <div className="filter-group">
              <label>Category</label>
              <select 
                className="filter-select" 
                value={selectedCategory} 
                onChange={(e) => {
                  setSelectedCategory(e.target.value);
                  setSelectedProduct(''); // clear product when category changes to avoid filter clashes
                }}
              >
                <option value="">All Categories</option>
                <option value="Skincare">Skincare</option>
                <option value="Haircare">Haircare</option>
                <option value="Makeup">Makeup</option>
              </select>
            </div>

            <div className="filter-group">
              <label>Product Filter</label>
              <select 
                className="filter-select" 
                value={selectedProduct} 
                onChange={(e) => setSelectedProduct(e.target.value)}
              >
                <option value="">All Products</option>
                {products.map(p => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>

            <div className="filter-group">
              <label>Start Date</label>
              <input 
                type="date" 
                className="filter-input"
                value={startDate}
                min="2025-01-01"
                max="2025-12-31"
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>

            <div className="filter-group">
              <label>End Date</label>
              <input 
                type="date" 
                className="filter-input"
                value={endDate}
                min="2025-01-01"
                max="2025-12-31"
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
          </div>
        )}

        {/* TAB 1: DASHBOARD */}
        {activeTab === 'dashboard' && (
          <div className="animate-fade-in">
            {dashboardLoading ? (
              <div style={{ textAlign: 'center', padding: '60px' }}>Loading Dashboard Metrics...</div>
            ) : (
              <>
                {/* KPI Metrics Summary Grid */}
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

                {/* Operations & Visual Mix */}
                <div className="charts-grid">
                  {/* Campaign ROI & Mix */}
                  <div className="chart-card">
                    <h3><Package size={16} /> Campaign Marketing Mix</h3>
                    <div style={{ height: '260px', position: 'relative', display: 'flex', justifyContent: 'center' }}>
                      {campaignChartConfig ? (
                        <Bar 
                          data={campaignChartConfig}
                          options={{
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: { legend: { display: false } },
                            scales: {
                              y: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                              x: { ticks: { color: '#9ca3af' }, grid: { display: false } }
                            }
                          }}
                        />
                      ) : <p>No Campaign Data Available</p>}
                    </div>
                  </div>

                  {/* Channel Mix share */}
                  <div className="chart-card">
                    <h3><Users size={16} /> Sales Channel Split</h3>
                    <div style={{ height: '220px', position: 'relative', display: 'flex', justifyContent: 'center' }}>
                      {channelChartConfig ? (
                        <Doughnut 
                          data={channelChartConfig}
                          options={{
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                              legend: {
                                position: 'bottom',
                                labels: { color: '#9ca3af', font: { family: 'Outfit' }, boxWidth: 12 }
                              }
                            }
                          }}
                        />
                      ) : <p>No Channel Data Available</p>}
                    </div>
                  </div>
                </div>

                {/* Inventory Alerts (If product is filtered) */}
                {selectedProduct && inventoryData && (
                  <div className="chart-card animate-fade-in" style={{ marginBottom: '28px' }}>
                    <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Package size={16} /> Product Inventory & Stockout Assessment ({selectedProduct})
                    </h3>
                    <div className="trend-stats" style={{ margin: '0' }}>
                      <div className="trend-stat-card">
                        <label>Current Stock</label>
                        <p>{formatNumber(inventoryData.current_stock)} units</p>
                      </div>
                      <div className="trend-stat-card">
                        <label>Average Period Stock</label>
                        <p>{formatNumber(inventoryData.average_stock.toFixed(0))}</p>
                      </div>
                      <div className="trend-stat-card">
                        <label>Estimated Coverage</label>
                        <p>{inventoryData.estimated_days_of_stock.toFixed(1)} days</p>
                      </div>
                      <div className="trend-stat-card" style={{ 
                        borderColor: inventoryData.stockout_risk === 'High' ? 'rgba(239, 68, 68, 0.4)' : 
                                     inventoryData.stockout_risk === 'Medium' ? 'rgba(245, 158, 11, 0.4)' : 'rgba(16, 185, 129, 0.4)'
                      }}>
                        <label>Stockout Risk</label>
                        <p style={{ 
                          color: inventoryData.stockout_risk === 'High' ? 'var(--danger)' : 
                                 inventoryData.stockout_risk === 'Medium' ? 'var(--warning)' : 'var(--success)'
                        }}>
                          {inventoryData.stockout_risk}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* TAB 2: TREND ANALYSIS */}
        {activeTab === 'trends' && (
          <div className="animate-fade-in">
            {trendsLoading ? (
              <div style={{ textAlign: 'center', padding: '60px' }}>Analyzing trajectories...</div>
            ) : (
              <div className="chart-card">
                {/* Configuration header */}
                <div className="trends-config">
                  <div className="filter-group">
                    <label>Target Metric</label>
                    <select 
                      className="filter-select"
                      value={trendMetric}
                      onChange={(e) => setTrendMetric(e.target.value)}
                    >
                      <option value="revenue">Revenue</option>
                      <option value="orders">Orders</option>
                      <option value="profit">Profit</option>
                      <option value="conversion_rate">Conversion Rate</option>
                      <option value="retention_rate">Retention Rate</option>
                      <option value="traffic">Traffic</option>
                    </select>
                  </div>
                  
                  <div className="filter-group">
                    <label>Time Step</label>
                    <div className="granularity-selector">
                      <button 
                        className={`granularity-btn ${trendGranularity === 'daily' ? 'active' : ''}`}
                        onClick={() => setTrendGranularity('daily')}
                      >
                        Daily
                      </button>
                      <button 
                        className={`granularity-btn ${trendGranularity === 'weekly' ? 'active' : ''}`}
                        onClick={() => setTrendGranularity('weekly')}
                      >
                        Weekly
                      </button>
                      <button 
                        className={`granularity-btn ${trendGranularity === 'monthly' ? 'active' : ''}`}
                        onClick={() => setTrendGranularity('monthly')}
                      >
                        Monthly
                      </button>
                      <button 
                        className={`granularity-btn ${trendGranularity === 'quarterly' ? 'active' : ''}`}
                        onClick={() => setTrendGranularity('quarterly')}
                      >
                        Quarterly
                      </button>
                    </div>
                  </div>
                </div>

                {/* Line graph */}
                <div style={{ height: '360px', position: 'relative' }}>
                  {trendChartConfig ? (
                    <Line 
                      data={trendChartConfig}
                      options={{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                          legend: { display: false }
                        },
                        scales: {
                          y: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                          x: { ticks: { color: '#9ca3af' }, grid: { display: false } }
                        }
                      }}
                    />
                  ) : <p style={{ textAlign: 'center', padding: '40px' }}>Loading Trend Data...</p>}
                </div>

                {/* Statistical Trend indicators */}
                {trendData && (
                  <div className="trend-stats animate-fade-in">
                    <div className="trend-stat-card">
                      <label>Regression Direction</label>
                      <p style={{ 
                        color: trendData.direction === 'increasing' ? 'var(--success)' : 
                               trendData.direction === 'decreasing' ? 'var(--danger)' : 'var(--text-primary)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px'
                      }}>
                        {trendData.direction === 'increasing' && <ArrowUpRight size={18} />}
                        {trendData.direction === 'decreasing' && <ArrowDownRight size={18} />}
                        {trendData.direction.toUpperCase()}
                      </p>
                    </div>
                    <div className="trend-stat-card">
                      <label>Period Growth Rate</label>
                      <p style={{ 
                        color: trendData.growth_rate_pct > 0 ? 'var(--success)' : 
                               trendData.growth_rate_pct < 0 ? 'var(--danger)' : 'var(--text-primary)'
                      }}>
                        {trendData.growth_rate_pct > 0 ? '+' : ''}{trendData.growth_rate_pct}%
                      </p>
                    </div>
                    <div className="trend-stat-card">
                      <label>R-Squared Fit</label>
                      <p>{(trendData.r_squared * 100).toFixed(2)}%</p>
                    </div>
                    <div className="trend-stat-card">
                      <label>Trend Confidence (P-value)</label>
                      <p>{trendData.p_value < 0.05 ? 'Significant (< 5%)' : 'Weak/No effect'}</p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* TAB 3: ANOMALIES */}
        {activeTab === 'anomalies' && (
          <div className="animate-fade-in">
            
            {/* Filter settings */}
            <div className="filter-bar">
              <div className="filter-group">
                <label>Target Date</label>
                <input 
                  type="date"
                  className="filter-input"
                  value={anomalyDate}
                  min="2025-01-15"
                  max="2025-12-31"
                  onChange={(e) => setAnomalyDate(e.target.value)}
                />
              </div>
              <div className="filter-group">
                <label>Target KPI</label>
                <select 
                  className="filter-select"
                  value={anomalyKpi}
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
              <div style={{ textAlign: 'center', padding: '60px' }}>Scanning historical records for anomalies...</div>
            ) : (
              <div className="anomalies-container">
                {/* Critical Products List */}
                <div className="anomalies-list-card">
                  <h3 style={{ fontSize: '15px', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '16px' }}>
                    Ranked Risk Products ({anomalyDate})
                  </h3>
                  
                  {anomalyReport?.top_10_critical_products?.length > 0 ? (
                    anomalyReport.top_10_critical_products.map((item, idx) => (
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
                  ) : <p style={{ fontSize: '14px', color: 'var(--text-muted)' }}>No products with high anomaly ratings found for this date.</p>}
                </div>

                {/* Anomaly Details Panel */}
                <div className="anomaly-detail-card">
                  {anomalyDetailsLoading ? (
                    <div style={{ textAlign: 'center', padding: '60px' }}>Executing 15-layer calculations...</div>
                  ) : anomalyDetails ? (
                    <div className="animate-fade-in">
                      
                      {/* Detail Header */}
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

                      {/* Expected vs Actual Comparison */}
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

                      {/* Business Rules Triggered */}
                      {anomalyDetails.business_rules_triggered?.length > 0 && (
                        <div className="detail-section">
                          <h4><AlertTriangle size={14} style={{ marginRight: '6px', color: 'var(--danger)', verticalAlign: 'middle' }} /> Triggered Rule Warnings</h4>
                          {anomalyDetails.business_rules_triggered.map(rule => (
                            <div key={rule.rule_id} className="rule-pill">
                              <strong>{rule.rule_id}</strong>: {rule.description}
                            </div>
                          ))}
                        </div>
                      )}

                      {/* SHAP Root Cause Drivers */}
                      {anomalyDetails.explanation?.top_drivers?.length > 0 && (
                        <div className="detail-section">
                          <h4><BookOpen size={14} style={{ marginRight: '6px', color: 'var(--primary-hover)', verticalAlign: 'middle' }} /> Attributed Outlier Drivers (RCA)</h4>
                          <div className="driver-bar-container">
                            {anomalyDetails.explanation.top_drivers.map((drv, idx) => {
                              // Normalize driving importance width percentage
                              const maxVal = Math.max(...anomalyDetails.explanation.top_drivers.map(d => Math.abs(d.shap_value)));
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

                      {/* Projected Business Loss Impact */}
                      {anomalyDetails.business_impact && (
                        <div className="detail-section" style={{ borderTop: '1px solid var(--border-color)', paddingTop: '16px', marginTop: '16px' }}>
                          <h4>Estimated Business Impact</h4>
                          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                            Expected Loss: <strong style={{ color: 'var(--danger)' }}>{formatCurrency(anomalyDetails.business_impact.revenue_loss_estimate || 0)}</strong>.
                            {anomalyDetails.business_impact.summary_explanation}
                          </p>
                        </div>
                      )}

                    </div>
                  ) : <p style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>Select a product on the left to view detailed root cause analysis.</p>}
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 5: INTELLIGENCE REPOSITORY */}
        {activeTab === 'repository' && (
          <div className="repository-container animate-fade-in">
            {/* Left explorer list */}
            <div className="anomalies-list-card">
              <div className="repository-tabs">
                <button 
                  className={`repository-tab-btn ${repoTab === 'reports' ? 'active' : ''}`}
                  onClick={() => setRepoTab('reports')}
                >
                  Archive
                </button>
                <button 
                  className={`repository-tab-btn ${repoTab === 'search' ? 'active' : ''}`}
                  onClick={() => setRepoTab('search')}
                >
                  Semantic Search
                </button>
                <button 
                  className={`repository-tab-btn ${repoTab === 'insights' ? 'active' : ''}`}
                  onClick={() => setRepoTab('insights')}
                >
                  Topic Insights
                </button>
              </div>

              {repoLoading ? (
                <div style={{ textAlign: 'center', padding: '60px' }}>Loading...</div>
              ) : (
                <div className="repository-list">
                  {repoTab === 'reports' && (
                    <>
                      <h4 style={{ fontSize: '12px', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '16px' }}>Inferred A/B Experiments</h4>
                      {experiments.length > 0 ? (
                        experiments.map((exp) => (
                          <div 
                            key={exp.id}
                            className={`anomaly-item ${selectedExperimentId === exp.id ? 'selected' : ''}`}
                            onClick={() => {
                              setSelectedExperimentId(exp.id);
                              fetchReportDetails(exp.id);
                            }}
                          >
                            <div style={{ flexGrow: 1, marginRight: '12px' }}>
                              <p style={{ fontWeight: '600', fontSize: '14px', margin: 0 }}>{exp.type}</p>
                              <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', margin: '4px 0 0 0' }}>
                                Product {exp.product_ids} | {exp.start_date}
                              </p>
                            </div>
                            <span className={`outcome-badge ${exp.outcome}`} style={{ fontSize: '10px' }}>
                              {exp.outcome}
                            </span>
                          </div>
                        ))
                      ) : (
                        <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>No historical experiments found.</p>
                      )}
                    </>
                  )}

                  {repoTab === 'search' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      <form onSubmit={handleRepoSearch} style={{ display: 'flex', gap: '8px' }}>
                        <input 
                          type="text"
                          className="filter-input"
                          style={{ flexGrow: 1, minWidth: 'auto' }}
                          placeholder="Search e.g. pricing, checkout..."
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                        />
                        <button type="submit" className="chat-send-btn" style={{ padding: '8px 14px', fontSize: '13px' }} disabled={searchLoading}>
                          Search
                        </button>
                      </form>
                      
                      <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                        <button onClick={() => { setSearchQuery('pricing experiments'); }} className="severity-tag low" style={{ cursor: 'pointer', border: 'none', background: 'rgba(255,255,255,0.04)' }}>"pricing"</button>
                        <button onClick={() => { setSearchQuery('checkout conversion'); }} className="severity-tag low" style={{ cursor: 'pointer', border: 'none', background: 'rgba(255,255,255,0.04)' }}>"checkout"</button>
                        <button onClick={() => { setSearchQuery('marketing campaigns'); }} className="severity-tag low" style={{ cursor: 'pointer', border: 'none', background: 'rgba(255,255,255,0.04)' }}>"marketing"</button>
                      </div>
                    </div>
                  )}

                  {repoTab === 'insights' && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                      <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: 0 }}>Select learning area to analyze patterns:</p>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                        {['pricing', 'checkout', 'discount', 'marketing'].map(t => (
                          <button
                            key={t}
                            className="nav-button"
                            style={{ 
                              justifyContent: 'center', 
                              backgroundColor: insightsTopic === t ? 'var(--primary-glow)' : 'rgba(255,255,255,0.02)',
                              color: insightsTopic === t ? 'var(--primary-hover)' : 'var(--text-secondary)',
                              border: insightsTopic === t ? '1px solid rgba(139, 92, 246, 0.2)' : '1px solid var(--border-color)',
                              padding: '10px'
                            }}
                            onClick={() => {
                              setInsightsTopic(t);
                              handleExtractInsights(t);
                            }}
                          >
                            {t.toUpperCase()}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Right details / results panel */}
            <div className="detail-drawer" style={{ maxHeight: '78vh', overflowY: 'auto' }}>
              {repoTab === 'reports' && (
                detailLoading ? (
                  <div style={{ textAlign: 'center', padding: '60px' }}>Reading report...</div>
                ) : selectedItemDetail ? (
                  <div className="animate-fade-in">
                    <div className="anomaly-detail-header" style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '16px', marginBottom: '20px' }}>
                      <div>
                        <h2 style={{ margin: 0, fontSize: '18px' }}>{experiments.find(e => e.id === selectedExperimentId)?.type}</h2>
                        <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px', margin: '4px 0 0 0' }}>
                          ID: {experiments.find(e => e.id === selectedExperimentId)?.experiment_id} | Product: {experiments.find(e => e.id === selectedExperimentId)?.product_ids}
                        </p>
                      </div>
                      <span className={`outcome-badge ${experiments.find(e => e.id === selectedExperimentId)?.outcome}`}>
                        {experiments.find(e => e.id === selectedExperimentId)?.outcome}
                      </span>
                    </div>

                    {experiments.find(e => e.id === selectedExperimentId) && (
                      <div className="detail-section">
                        <h4 style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-secondary)', marginBottom: '8px' }}>Pre vs. Post KPI Shifts</h4>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '10px' }}>
                          {Object.keys(experiments.find(e => e.id === selectedExperimentId).before_metrics).map(kpi => {
                            const before = experiments.find(e => e.id === selectedExperimentId).before_metrics[kpi];
                            const after = experiments.find(e => e.id === selectedExperimentId).after_metrics[kpi];
                            const pct = before > 0 ? ((after - before) / before * 100).toFixed(1) : '0.0';
                            return (
                              <div key={kpi} className="trend-stat-card" style={{ padding: '8px 12px', textAlign: 'center' }}>
                                <label style={{ fontSize: '10px', textTransform: 'capitalize' }}>{kpi.replace('_rate', '').replace('_', ' ')}</label>
                                <p style={{ fontSize: '13px', fontWeight: 'bold', color: parseFloat(pct) > 0 ? 'var(--success)' : parseFloat(pct) < 0 ? 'var(--danger)' : 'var(--text-primary)' }}>
                                  {parseFloat(pct) > 0 ? '+' : ''}{pct}%
                                </p>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    <div className="detail-section" style={{ marginTop: '20px', borderTop: '1px solid var(--border-color)', paddingTop: '16px' }}>
                      <h4 style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-secondary)', marginBottom: '10px' }}>Business Summary Report</h4>
                      <div 
                        className="chat-bubble assistant" 
                        style={{ width: '100%', maxWidth: '100%', padding: '16px', border: '1px solid var(--border-color)', borderRadius: '10px', backgroundColor: 'rgba(255,255,255,0.01)' }}
                        dangerouslySetInnerHTML={{ __html: renderMarkdown(selectedItemDetail.human_readable_text) }}
                      />
                    </div>
                  </div>
                ) : (
                  <p style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>Select an experiment on the left to read audit reports.</p>
                )
              )}

              {repoTab === 'search' && (
                searchLoading ? (
                  <div style={{ textAlign: 'center', padding: '60px' }}>Searching...</div>
                ) : searchResults ? (
                  <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    <h3 style={{ fontSize: '15px', color: 'var(--text-secondary)', textTransform: 'uppercase', margin: 0 }}>
                      Matched results (found {searchResults.results.length})
                    </h3>
                    {searchResults.results.map((res, idx) => (
                      <div key={idx} className="chart-card" style={{ padding: '16px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '10px', marginBottom: '12px' }}>
                          <div>
                            <h4 style={{ margin: 0, fontSize: '15px' }}>{res.experiment.type}</h4>
                            <p style={{ fontSize: '11px', color: 'var(--text-muted)', margin: '4px 0 0 0' }}>
                              Product {res.experiment.product_ids} | Dates: {res.experiment.start_date} - {res.experiment.end_date}
                            </p>
                          </div>
                          <div style={{ textAlign: 'right' }}>
                            <span className="severity-tag medium" style={{ background: 'var(--primary-glow)', color: 'var(--primary-hover)', fontSize: '10px' }}>
                              Match: {(res.score * 100).toFixed(0)}%
                            </span>
                            <span className={`outcome-badge ${res.experiment.outcome}`} style={{ marginLeft: '6px', fontSize: '10px' }}>
                              {res.experiment.outcome}
                            </span>
                          </div>
                        </div>
                        <p style={{ fontSize: '13px', margin: 0, color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                          <strong>Findings:</strong> {res.structured_json?.learnings || 'No summary learnings catalogued.'}
                        </p>
                        <p style={{ fontSize: '13px', margin: '8px 0 0 0', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                          <strong>Recommendation:</strong> {res.structured_json?.recommendations || 'No recommendations logged.'}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>Type query on the left to run semantic vector similarity search.</p>
                )
              )}

              {repoTab === 'insights' && (
                insightsLoading ? (
                  <div style={{ textAlign: 'center', padding: '60px' }}>Analyzing...</div>
                ) : insightsResult ? (
                  <div className="insights-card animate-fade-in" style={{ margin: 0 }}>
                    <div className="insights-header">
                      <div>
                        <h3 style={{ margin: 0, fontSize: '16px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <Sparkles size={16} style={{ color: 'var(--warning)' }} /> Recurring Learnings: "{insightsTopic.toUpperCase()}"
                        </h3>
                        <p style={{ fontSize: '11px', color: 'var(--text-muted)', margin: '4px 0 0 0' }}>
                          Synthesized across database experiments (Confidence: {(insightsResult.confidence_score*100).toFixed(0)}%)
                        </p>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Historical Success:</span>
                        <div style={{ fontSize: '24px', fontWeight: '800', color: 'var(--success)' }}>
                          {insightsResult.synthesized_rules.success_rate_pct}%
                        </div>
                      </div>
                    </div>

                    <div style={{ borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '12px', marginTop: '12px' }}>
                      <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.5', margin: '0 0 16px 0' }}>
                        {insightsResult.synthesized_rules.learnings}
                      </p>

                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                        <div>
                          <h4 style={{ fontSize: '12px', color: 'var(--success)', margin: '0 0 8px 0', textTransform: 'uppercase' }}>Successful Tactics</h4>
                          <ul style={{ paddingLeft: '16px', margin: 0, color: 'var(--text-muted)', fontSize: '12px', lineHeight: '1.4' }}>
                            {insightsResult.synthesized_rules.successful_strategies.map((s, idx) => (
                              <li key={idx} style={{ marginBottom: '6px' }}>{s}</li>
                            ))}
                          </ul>
                        </div>
                        <div>
                          <h4 style={{ fontSize: '12px', color: 'var(--danger)', margin: '0 0 8px 0', textTransform: 'uppercase' }}>Failure Risks</h4>
                          <ul style={{ paddingLeft: '16px', margin: 0, color: 'var(--text-muted)', fontSize: '12px', lineHeight: '1.4' }}>
                            {insightsResult.synthesized_rules.frequent_failures.map((f, idx) => (
                              <li key={idx} style={{ marginBottom: '6px' }}>{f}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>Select a learning topic on the left to extract repository-wide patterns.</p>
                )
              )}
            </div>
          </div>
        )}

        {/* TAB 4: AI ASSISTANT CHAT */}
        {activeTab === 'assistant' && (
          <div className="chat-container animate-fade-in">
            {/* Messages box */}
            <div className="chat-messages">
              {messages.map((msg, index) => (
                <div key={index} className={`chat-bubble ${msg.sender}`}>
                  {msg.sender === 'assistant' ? (
                    <div 
                      dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.text) }} 
                    />
                  ) : (
                    msg.text
                  )}
                  {msg.meta && (
                    <div style={{ marginTop: '8px', fontSize: '11px', color: 'var(--text-muted)', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '6px' }}>
                      Routed to: <code>{msg.meta.route}</code>
                    </div>
                  )}
                </div>
              ))}
              {chatLoading && (
                <div className="chat-bubble assistant" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <RefreshCw size={14} className="spin" />
                  Generating executive summaries and evaluating calculations...
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input field */}
            <form className="chat-input-container" onSubmit={handleSendMessage}>
              <input 
                type="text"
                className="chat-input"
                placeholder="Ask e.g.: 'Why did revenue drop for P001 on 2025-12-31?' or 'What happens if discount increases by 10%?'"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                disabled={chatLoading}
              />
              <button 
                type="submit" 
                className="chat-send-btn"
                disabled={chatLoading || !chatInput.trim()}
              >
                Send
              </button>
            </form>
          </div>
        )}

      </div>
    </div>
  );
}
