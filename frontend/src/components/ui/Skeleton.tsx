import React from 'react';

interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  className?: string;
  variant?: 'text' | 'rect' | 'circle';
}

export const Skeleton: React.FC<SkeletonProps> = ({
  width = '100%',
  height = 16,
  className = '',
  variant = 'rect',
}) => (
  <div
    className={`skeleton skeleton-${variant} ${className}`}
    style={{ width, height }}
    aria-hidden
  />
);

export const DashboardSkeleton: React.FC = () => (
  <div className="skeleton-dashboard animate-fade-in">
    <div className="metrics-grid">
      {[1, 2, 3, 4, 5].map(i => (
        <div key={i} className="card card-pad-md">
          <Skeleton height={14} width="60%" />
          <Skeleton height={32} width="80%" className="skeleton-mt" />
          <Skeleton height={12} width="45%" className="skeleton-mt-sm" />
        </div>
      ))}
    </div>
    <div className="bento-grid">
      <div className="card card-pad-lg bento-wide">
        <Skeleton height={20} width="40%" />
        <Skeleton height={280} className="skeleton-mt-lg" />
      </div>
      <div className="card card-pad-lg">
        <Skeleton height={20} width="55%" />
        <Skeleton height={220} className="skeleton-mt-lg" variant="circle" />
      </div>
    </div>
  </div>
);

export const TableSkeleton: React.FC<{ rows?: number }> = ({ rows = 5 }) => (
  <div className="table-skeleton">
    <div className="table-skeleton-header">
      {[1, 2, 3, 4].map(i => <Skeleton key={i} height={12} />)}
    </div>
    {Array.from({ length: rows }).map((_, i) => (
      <div key={i} className="table-skeleton-row">
        {[1, 2, 3, 4].map(j => <Skeleton key={j} height={14} />)}
      </div>
    ))}
  </div>
);
