import React, { useState } from 'react';
import { Sparkles, RefreshCw } from 'lucide-react';
import { renderMarkdown } from '../utils/mdRenderer';
import { useExperiments, useReportDetails, useRepositorySearch, useTopicInsights } from '../hooks/useExperiments';
import { LoadingState, ErrorState } from '../components/LoadingErrorState';

export default function ExperimentsPage() {
  const [repoTab, setRepoTab] = useState('reports');
  
  // Archive State
  const [selectedExperimentId, setSelectedExperimentId] = useState<number | null>(null);
  const { data: experiments = [], isLoading: repoLoading, isError: isRepoError, error: repoError, refetch: refetchRepo } = useExperiments();
  const { data: selectedItemDetail, isFetching: detailLoading, isError: isDetailError, error: detailError, refetch: refetchDetail } = useReportDetails(selectedExperimentId);

  // Search State
  const [searchQuery, setSearchQuery] = useState('');
  const { data: searchResults, isFetching: searchLoading, isError: isSearchError, error: searchError, refetch: refetchSearch } = useRepositorySearch(searchQuery);

  // Insights State
  const [insightsTopic, setInsightsTopic] = useState('pricing');
  const { data: insightsResult, isFetching: insightsLoading, isError: isInsightsError, error: insightsError, refetch: refetchInsights } = useTopicInsights(insightsTopic);

  const handleRepoSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) refetchSearch();
  };

  const handleExtractInsights = (topic: string) => {
    setInsightsTopic(topic);
    // Since useTopicInsights depends on insightsTopic, it will automatically refetch.
  };

  return (
    <>
      <div className="header">
        <div>
          <h1>Historical Intelligence Repository</h1>
          <p>Search past experiments, reports, and extracted learnings</p>
        </div>
        <button onClick={() => refetchRepo()} className="filter-select" style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
          <RefreshCw size={14} /> Sync Repository
        </button>
      </div>

      <div className="repository-container animate-fade-in">
        <div className="anomalies-list-card">
          <div className="repository-tabs">
            <button className={`repository-tab-btn ${repoTab === 'reports' ? 'active' : ''}`} onClick={() => setRepoTab('reports')}>Archive</button>
            <button className={`repository-tab-btn ${repoTab === 'search' ? 'active' : ''}`} onClick={() => setRepoTab('search')}>Semantic Search</button>
            <button className={`repository-tab-btn ${repoTab === 'insights' ? 'active' : ''}`} onClick={() => setRepoTab('insights')}>Topic Insights</button>
          </div>

          {repoLoading ? <LoadingState message="Loading repository archive..." /> : isRepoError ? <ErrorState message={repoError?.message} onRetry={() => refetchRepo()} /> : (
            <div className="repository-list">
              {repoTab === 'reports' && (
                <>
                  <h4 style={{ fontSize: '12px', color: 'var(--text-secondary)', textTransform: 'uppercase', marginBottom: '16px' }}>Inferred A/B Experiments</h4>
                  {experiments.map((exp: any) => (
                    <div 
                      key={exp.id}
                      className={`anomaly-item ${selectedExperimentId === exp.id ? 'selected' : ''}`}
                      onClick={() => setSelectedExperimentId(exp.id)}
                    >
                      <div style={{ flexGrow: 1, marginRight: '12px' }}>
                        <p style={{ fontWeight: '600', fontSize: '14px', margin: 0 }}>{exp.type}</p>
                        <p style={{ fontSize: '11px', color: 'var(--text-muted)', margin: '4px 0 0 0' }}>Product {exp.product_ids} | {exp.start_date}</p>
                      </div>
                      <span className={`outcome-badge ${exp.outcome}`} style={{ fontSize: '10px' }}>{exp.outcome}</span>
                    </div>
                  ))}
                </>
              )}

              {repoTab === 'search' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <form onSubmit={handleRepoSearch} style={{ display: 'flex', gap: '8px' }}>
                    <input 
                      type="text" className="filter-input" style={{ flexGrow: 1, minWidth: 'auto' }}
                      placeholder="Search e.g. pricing, checkout..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
                    />
                    <button type="submit" className="chat-send-btn" style={{ padding: '8px 14px', fontSize: '13px' }} disabled={searchLoading}>Search</button>
                  </form>
                  <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                    {['pricing experiments', 'checkout conversion', 'marketing campaigns'].map(t => (
                      <button key={t} onClick={() => { setSearchQuery(t); setTimeout(() => refetchSearch(), 100); }} className="severity-tag low" style={{ cursor: 'pointer', border: 'none', background: 'rgba(255,255,255,0.04)' }}>"{t.split(' ')[0]}"</button>
                    ))}
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
                        style={{ justifyContent: 'center', backgroundColor: insightsTopic === t ? 'var(--primary-glow)' : 'rgba(255,255,255,0.02)', color: insightsTopic === t ? 'var(--primary-hover)' : 'var(--text-secondary)', border: insightsTopic === t ? '1px solid rgba(139, 92, 246, 0.2)' : '1px solid var(--border-color)', padding: '10px' }}
                        onClick={() => handleExtractInsights(t)}
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

        <div className="detail-drawer" style={{ maxHeight: '78vh', overflowY: 'auto' }}>
          {repoTab === 'reports' && (
            detailLoading ? <LoadingState message="Reading report details..." /> : isDetailError ? <ErrorState message={detailError?.message} onRetry={() => refetchDetail()} /> : selectedItemDetail ? (
              <div className="animate-fade-in">
                <div className="anomaly-detail-header" style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '16px', marginBottom: '20px' }}>
                  <div>
                    <h2 style={{ margin: 0, fontSize: '18px' }}>{experiments.find((e: any) => e.id === selectedExperimentId)?.type}</h2>
                  </div>
                </div>
                <div className="detail-section" style={{ marginTop: '20px', borderTop: '1px solid var(--border-color)', paddingTop: '16px' }}>
                  <h4 style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-secondary)', marginBottom: '10px' }}>Business Summary Report</h4>
                  <div className="chat-bubble assistant" style={{ width: '100%', maxWidth: '100%', padding: '16px', border: '1px solid var(--border-color)', borderRadius: '10px', backgroundColor: 'rgba(255,255,255,0.01)' }} dangerouslySetInnerHTML={{ __html: renderMarkdown(selectedItemDetail.human_readable_text) }} />
                </div>
              </div>
            ) : <p style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>Select an experiment to read audit reports.</p>
          )}

          {repoTab === 'search' && (
            searchLoading ? <LoadingState message="Running semantic search..." /> : isSearchError ? <ErrorState message={searchError?.message} onRetry={() => refetchSearch()} /> : searchResults ? (
              <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <h3 style={{ fontSize: '15px', color: 'var(--text-secondary)', textTransform: 'uppercase', margin: 0 }}>Matched results (found {searchResults.results.length})</h3>
                {searchResults.results.map((res: any, idx: number) => (
                  <div key={idx} className="chart-card" style={{ padding: '16px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '10px', marginBottom: '12px' }}>
                      <h4 style={{ margin: 0, fontSize: '15px' }}>{res.experiment.type}</h4>
                    </div>
                    <p style={{ fontSize: '13px', margin: 0, color: 'var(--text-secondary)' }}><strong>Findings:</strong> {res.structured_json?.learnings}</p>
                  </div>
                ))}
              </div>
            ) : <p style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>Type query to run semantic vector similarity search.</p>
          )}

          {repoTab === 'insights' && (
            insightsLoading ? <LoadingState message={`Extracting insights across ${insightsTopic}...`} /> : isInsightsError ? <ErrorState message={insightsError?.message} onRetry={() => refetchInsights()} /> : insightsResult ? (
              <div className="insights-card animate-fade-in" style={{ margin: 0 }}>
                <div className="insights-header">
                  <div>
                    <h3 style={{ margin: 0, fontSize: '16px', display: 'flex', alignItems: 'center', gap: '6px' }}><Sparkles size={16} style={{ color: 'var(--warning)' }} /> Recurring Learnings</h3>
                  </div>
                </div>
                <div style={{ borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '12px', marginTop: '12px' }}>
                  <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.5', margin: '0 0 16px 0' }}>{insightsResult.synthesized_rules.learnings}</p>
                </div>
              </div>
            ) : <p style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>Select a learning topic to extract repository-wide patterns.</p>
          )}
        </div>
      </div>
    </>
  );
}
