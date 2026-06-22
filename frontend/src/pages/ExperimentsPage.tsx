import React, { useState } from 'react';
import { Sparkles, RefreshCw, BookMarked, Search } from 'lucide-react';
import { MarkdownBody } from '../components/MarkdownBody';
import { useExperiments, useReportDetails, useRepositorySearch, useTopicInsights } from '../hooks/useExperiments';
import { LoadingState, ErrorState } from '../components/LoadingErrorState';
import { Button } from '../components/ui/Button';

export default function ExperimentsPage() {
  const [repoTab, setRepoTab] = useState('reports');

  const [selectedExperimentId, setSelectedExperimentId] = useState<number | null>(null);
  const { data: experiments = [], isLoading: repoLoading, isError: isRepoError, error: repoError, refetch: refetchRepo } = useExperiments();
  const { data: selectedItemDetail, isFetching: detailLoading, isError: isDetailError, error: detailError, refetch: refetchDetail } = useReportDetails(selectedExperimentId);

  const [searchQuery, setSearchQuery] = useState('');
  const { data: searchResults, isFetching: searchLoading, isError: isSearchError, error: searchError, refetch: refetchSearch } = useRepositorySearch(searchQuery);

  const [insightsTopic, setInsightsTopic] = useState('pricing');
  const { data: insightsResult, isFetching: insightsLoading, isError: isInsightsError, error: insightsError, refetch: refetchInsights } = useTopicInsights(insightsTopic);

  const handleRepoSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) refetchSearch();
  };

  const handleExtractInsights = (topic: string) => {
    setInsightsTopic(topic);
  };

  return (
    <>
      <header className="pin-hero animate-fade-in">
        <div>
          <div className="pin-hero-eyebrow">
            <BookMarked size={14} />
            Memory lane
          </div>
          <h1>Your experiment scrapbook</h1>
          <p className="pin-hero-desc">
            Past tests, reports, and learnings — saved like pins on a board. Search by topic or browse what worked (and what didn&apos;t).
          </p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          icon={<RefreshCw size={14} />}
          onClick={() => refetchRepo()}
        >
          Sync archive
        </Button>
      </header>

      <div className="repo-scrapbook animate-fade-in">
        <div className="repo-pin-board">
          <div className="repo-tabs">
            <button className={`repo-tab ${repoTab === 'reports' ? 'active' : ''}`} onClick={() => setRepoTab('reports')}>
              Archive
            </button>
            <button className={`repo-tab ${repoTab === 'search' ? 'active' : ''}`} onClick={() => setRepoTab('search')}>
              Search
            </button>
            <button className={`repo-tab ${repoTab === 'insights' ? 'active' : ''}`} onClick={() => setRepoTab('insights')}>
              Patterns
            </button>
          </div>

          {repoLoading ? (
            <LoadingState message="Opening your archive…" />
          ) : isRepoError ? (
            <ErrorState message={repoError?.message} onRetry={() => refetchRepo()} />
          ) : (
            <div>
              {repoTab === 'reports' && (
                <>
                  <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 16 }}>Inferred A/B experiments</p>
                  {experiments.map((exp: { id: number; type: string; product_ids: string; start_date: string; outcome: string }) => (
                    <div
                      key={exp.id}
                      className={`pin-list-item ${selectedExperimentId === exp.id ? 'selected' : ''}`}
                      onClick={() => setSelectedExperimentId(exp.id)}
                    >
                      <div style={{ flexGrow: 1, marginRight: 12 }}>
                        <p style={{ fontWeight: 600, fontSize: 14, margin: 0 }}>{exp.type}</p>
                        <p style={{ fontSize: 11, color: 'var(--text-muted)', margin: '4px 0 0' }}>
                          Product {exp.product_ids} · {exp.start_date}
                        </p>
                      </div>
                      <span className={`outcome-badge ${exp.outcome}`} style={{ fontSize: 10 }}>
                        {exp.outcome}
                      </span>
                    </div>
                  ))}
                </>
              )}

              {repoTab === 'search' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  <form onSubmit={handleRepoSearch} style={{ display: 'flex', gap: 8 }}>
                    <input
                      type="text"
                      className="filter-input"
                      style={{ flexGrow: 1, minWidth: 'auto' }}
                      placeholder="Try pricing, checkout, campaigns…"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                    <button type="submit" className="chat-send-btn" style={{ padding: '8px 14px', fontSize: 13 }} disabled={searchLoading}>
                      <Search size={14} />
                    </button>
                  </form>
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {['pricing experiments', 'checkout conversion', 'marketing campaigns'].map((t) => (
                      <button
                        key={t}
                        type="button"
                        onClick={() => {
                          setSearchQuery(t);
                          setTimeout(() => refetchSearch(), 100);
                        }}
                        className="workspace-chip"
                        style={{ fontSize: 12 }}
                      >
                        {t.split(' ')[0]}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {repoTab === 'insights' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  <p style={{ fontSize: 13, color: 'var(--text-secondary)', margin: 0 }}>
                    Pick a topic to surface recurring patterns:
                  </p>
                  <div className="repo-topic-grid">
                    {['pricing', 'checkout', 'discount', 'marketing'].map((t) => (
                      <button
                        key={t}
                        type="button"
                        className={`repo-topic-btn ${insightsTopic === t ? 'active' : ''}`}
                        onClick={() => handleExtractInsights(t)}
                      >
                        {t}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="repo-detail">
          {repoTab === 'reports' &&
            (detailLoading ? (
              <LoadingState message="Reading report…" />
            ) : isDetailError ? (
              <ErrorState message={detailError?.message} onRetry={() => refetchDetail()} />
            ) : selectedItemDetail ? (
              <div className="animate-fade-in">
                <div className="repo-report-header">
                  <h2>{experiments.find((e: { id: number }) => e.id === selectedExperimentId)?.type}</h2>
                </div>
                <p className="repo-report-section-label">Business summary</p>
                <div className="report-card">
                  <MarkdownBody content={selectedItemDetail.human_readable_text} />
                </div>
              </div>
            ) : (
              <p style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                Select an experiment from the board to read its report.
              </p>
            ))}

          {repoTab === 'search' &&
            (searchLoading ? (
              <LoadingState message="Searching your archive…" />
            ) : isSearchError ? (
              <ErrorState message={searchError?.message} onRetry={() => refetchSearch()} />
            ) : searchResults ? (
              <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                <h3 style={{ fontSize: 15, color: 'var(--text-secondary)', margin: 0 }}>
                  {searchResults.results.length} matches found
                </h3>
                {searchResults.results.map((res: { experiment: { type: string }; structured_json?: { learnings?: string } }, idx: number) => (
                  <div key={idx} className="pin-card pin-card--pad">
                    <h4 style={{ margin: '0 0 10px', fontFamily: 'var(--font-display)' }}>{res.experiment.type}</h4>
                    <p style={{ fontSize: 13, margin: 0, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                      {res.structured_json?.learnings}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                Type a query to search across past experiments.
              </p>
            ))}

          {repoTab === 'insights' &&
            (insightsLoading ? (
              <LoadingState message={`Finding ${insightsTopic} patterns…`} />
            ) : isInsightsError ? (
              <ErrorState message={insightsError?.message} onRetry={() => refetchInsights()} />
            ) : insightsResult ? (
              <div className="repo-insights animate-fade-in">
                <h3 style={{ margin: '0 0 12px', fontSize: 18, display: 'flex', alignItems: 'center', gap: 8, fontFamily: 'var(--font-display)' }}>
                  <Sparkles size={18} style={{ color: 'var(--cozy-rose)' }} />
                  Recurring learnings
                </h3>
                <p style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.65, margin: 0 }}>
                  {insightsResult.synthesized_rules.learnings}
                </p>
              </div>
            ) : (
              <p style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                Choose a topic to extract patterns from your history.
              </p>
            ))}
        </div>
      </div>
    </>
  );
}
