import React from 'react';

interface ThinkingIndicatorProps {
  logs: string[];
}

export const ThinkingIndicator: React.FC<ThinkingIndicatorProps> = ({ logs }) => {
  const activeIndex = logs.length > 0 ? logs.length - 1 : -1;

  return (
    <div className="thinking-panel" aria-live="polite" aria-busy="true">
      <div className="thinking-panel__header">
        <div className="thinking-dots" aria-hidden>
          <span />
          <span />
          <span />
        </div>
        <div>
          <p className="thinking-panel__title">Working on your question</p>
          <p className="thinking-panel__subtitle">
            {logs.length > 0 ? logs[activeIndex] : 'Connecting to the analysis engine…'}
          </p>
        </div>
      </div>

      {logs.length > 0 && (
        <ol className="thinking-steps">
          {logs.map((log, idx) => {
            const isActive = idx === activeIndex;
            const isDone = idx < activeIndex;
            return (
              <li
                key={`${idx}-${log.slice(0, 24)}`}
                className={`thinking-step ${isActive ? 'thinking-step--active' : ''} ${isDone ? 'thinking-step--done' : ''}`}
              >
                <span className="thinking-step__marker" aria-hidden>
                  {isDone ? '✓' : isActive ? '·' : ''}
                </span>
                <span className="thinking-step__text">{log}</span>
              </li>
            );
          })}
        </ol>
      )}
    </div>
  );
};
