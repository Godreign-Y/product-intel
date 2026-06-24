import React, { useEffect, useRef } from 'react';
import { HypothesisProgressItem } from '../types';

interface HypothesisTrackerProps {
  items: HypothesisProgressItem[];
  notices: string[];
}

const verdictLabel: Record<string, string> = {
  pending: 'Queued',
  validating: 'Validating…',
  supported: 'Supported',
  inconclusive: 'Not validated',
  contradicted: 'Contradicted',
};

const verdictClass: Record<string, string> = {
  pending: 'hypothesis-item--pending',
  validating: 'hypothesis-item--validating',
  supported: 'hypothesis-item--supported',
  inconclusive: 'hypothesis-item--inconclusive',
  contradicted: 'hypothesis-item--contradicted',
};

export const HypothesisTracker: React.FC<HypothesisTrackerProps> = ({ items, notices }) => {
  const listRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [items.length, notices.length]);

  if (items.length === 0 && notices.length === 0) return null;

  const isGenerating = items.length === 0 && notices.some((n) => /generating/i.test(n));

  return (
    <div className="hypothesis-tracker" aria-live="polite">
      <p className="hypothesis-tracker__title">
        Hypothesis validation
        {isGenerating && <span className="hypothesis-tracker__processing"> — processing…</span>}
      </p>

      {notices.length > 0 && (
        <ul className="hypothesis-notices">
          {notices.map((note, i) => (
            <li key={`${i}-${note.slice(0, 24)}`} className="hypothesis-notice">
              {note}
            </li>
          ))}
        </ul>
      )}

      {items.length > 0 && (
        <div className="hypothesis-list" ref={listRef}>
          {items.map((item) => (
            <div
              key={item.hypothesis_id}
              className={`hypothesis-item ${verdictClass[item.status] || ''}`}
            >
              <div className="hypothesis-item__row">
                <span className="hypothesis-item__badge">{verdictLabel[item.status] || item.status}</span>
                <span className="hypothesis-item__title">{item.title}</span>
              </div>
              {item.overall_confidence != null && item.status !== 'pending' && item.status !== 'validating' && (
                <span className="hypothesis-item__meta">
                  Confidence {Math.round(item.overall_confidence * 100)}%
                  {item.confidence_band ? ` · ${item.confidence_band} band` : ''}
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
