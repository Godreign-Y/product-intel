import React from 'react';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { KPICardData } from '../types/dashboard';

interface KPICardProps {
  data: KPICardData;
}

export const KPICard: React.FC<KPICardProps> = ({ data }) => {
  const { title, value, changePercent, isPositive, timeframe, sparkline } = data;

  // Generate SVG path for sparkline
  const points = sparkline.map(p => p.value);
  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min === 0 ? 1 : max - min;
  
  const width = 140;
  const height = 30; // Shorter height to fit in 140px card
  const svgPoints = sparkline
    .map((p, index) => {
      const x = (index / (sparkline.length - 1)) * width;
      const y = height - ((p.value - min) / range) * (height - 6) - 3;
      return `${x},${y}`;
    })
    .join(' ');

  const strokeColor = isPositive ? '#10B981' : '#EF4444'; // Success green or Danger red
  const gradientId = `gradient-${data.id}-${title.replace(/\s+/g, '-')}`;

  return (
    <div className="bg-white rounded-[20px] border border-[#E5E7EB] p-4.5 shadow-sm hover:shadow-md transition-all duration-200 flex flex-col justify-between h-[140px] group overflow-hidden">
      <div>
        <div className="flex justify-between items-start">
          <span className="text-[13px] font-semibold text-[#6B7280] truncate max-w-[120px]" title={title}>{title}</span>
          <div
            className={`flex items-center text-[10px] font-bold px-2 py-0.5 rounded-full ${
              isPositive ? 'bg-emerald-50 text-[#10B981]' : 'bg-rose-50 text-[#EF4444]'
            }`}
          >
            {isPositive ? (
              <ArrowUpRight className="w-3 h-3 mr-0.5" />
            ) : (
              <ArrowDownRight className="w-3 h-3 mr-0.5" />
            )}
            {Math.abs(changePercent)}%
          </div>
        </div>

        <div className="mt-1 flex items-baseline">
          <span className="text-xl font-extrabold text-[#111827] tracking-tight">{value}</span>
        </div>
      </div>

      <div className="flex items-center justify-between gap-4">
        <span className="text-[10px] text-[#9CA3AF] whitespace-nowrap">{timeframe}</span>
        <div className="w-24 h-8 flex-shrink-0">
          <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full overflow-visible">
            <defs>
              <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={strokeColor} stopOpacity="0.2" />
                <stop offset="100%" stopColor={strokeColor} stopOpacity="0.0" />
              </linearGradient>
            </defs>
            {/* Area under the line */}
            <polygon
              points={`0,${height} ${svgPoints} ${width},${height}`}
              fill={`url(#${gradientId})`}
            />
            {/* The sparkline */}
            <polyline
              fill="none"
              stroke={strokeColor}
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              points={svgPoints}
            />
          </svg>
        </div>
      </div>
    </div>
  );
};
