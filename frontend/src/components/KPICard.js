import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';
export const KPICard = ({ data }) => {
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
    return (_jsxs("div", { className: "bg-white rounded-[20px] border border-[#E5E7EB] p-4.5 shadow-sm hover:shadow-md transition-all duration-200 flex flex-col justify-between h-[140px] group overflow-hidden", children: [_jsxs("div", { children: [_jsxs("div", { className: "flex justify-between items-start", children: [_jsx("span", { className: "text-[13px] font-semibold text-[#6B7280] truncate max-w-[120px]", title: title, children: title }), _jsxs("div", { className: `flex items-center text-[10px] font-bold px-2 py-0.5 rounded-full ${isPositive ? 'bg-emerald-50 text-[#10B981]' : 'bg-rose-50 text-[#EF4444]'}`, children: [isPositive ? (_jsx(ArrowUpRight, { className: "w-3 h-3 mr-0.5" })) : (_jsx(ArrowDownRight, { className: "w-3 h-3 mr-0.5" })), Math.abs(changePercent), "%"] })] }), _jsx("div", { className: "mt-1 flex items-baseline", children: _jsx("span", { className: "text-xl font-extrabold text-[#111827] tracking-tight", children: value }) })] }), _jsxs("div", { className: "flex items-center justify-between gap-4", children: [_jsx("span", { className: "text-[10px] text-[#9CA3AF] whitespace-nowrap", children: timeframe }), _jsx("div", { className: "w-24 h-8 flex-shrink-0", children: _jsxs("svg", { viewBox: `0 0 ${width} ${height}`, className: "w-full h-full overflow-visible", children: [_jsx("defs", { children: _jsxs("linearGradient", { id: gradientId, x1: "0", y1: "0", x2: "0", y2: "1", children: [_jsx("stop", { offset: "0%", stopColor: strokeColor, stopOpacity: "0.2" }), _jsx("stop", { offset: "100%", stopColor: strokeColor, stopOpacity: "0.0" })] }) }), _jsx("polygon", { points: `0,${height} ${svgPoints} ${width},${height}`, fill: `url(#${gradientId})` }), _jsx("polyline", { fill: "none", stroke: strokeColor, strokeWidth: "2", strokeLinecap: "round", strokeLinejoin: "round", points: svgPoints })] }) })] })] }));
};
