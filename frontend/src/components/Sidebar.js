import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Brain, FlaskConical, LineChart, Lightbulb, Settings, } from 'lucide-react';
export const Sidebar = () => {
    const { pathname } = useLocation();
    const menuItems = [
        { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
        { name: 'AI Workspace', path: '/ai-workspace', icon: Brain },
        { name: 'Experiments', path: '/experiments', icon: FlaskConical },
        { name: 'Predictions', path: '/predictions', icon: LineChart },
        { name: 'Recommendations', path: '/recommendations', icon: Lightbulb },
        { name: 'Settings', path: '/settings', icon: Settings },
    ];
    return (_jsxs("aside", { className: "w-[280px] bg-white text-[#111827] flex flex-col justify-between border-r border-[#E5E7EB] h-screen sticky top-0 flex-shrink-0 z-50", children: [_jsxs("div", { children: [_jsx("div", { className: "p-6 border-b border-[#E5E7EB]", children: _jsxs(Link, { to: "/dashboard", className: "flex items-center gap-2.5 group", children: [_jsx("div", { className: "w-8 h-8 rounded-lg bg-[#7C3AED] flex items-center justify-center shadow-lg group-hover:bg-[#6D28D9] transition-all duration-150", children: _jsx("span", { className: "font-extrabold text-white text-base", children: "\u03C0" }) }), _jsxs("div", { children: [_jsx("h1", { className: "font-bold text-sm tracking-wide text-[#111827] leading-tight", children: "Product" }), _jsx("p", { className: "text-[10px] text-[#7C3AED] font-bold tracking-widest uppercase", children: "Intelligence System" })] })] }) }), _jsx("nav", { className: "px-4 py-6 space-y-1.5", children: menuItems.map((item) => {
                            const isActive = item.path === '/dashboard'
                                ? pathname === '/' || pathname === '/dashboard'
                                : pathname.startsWith(item.path);
                            const Icon = item.icon;
                            return (_jsxs(Link, { to: item.path, className: `flex items-center gap-3 px-4 py-3 rounded-[12px] h-[44px] text-sm font-semibold transition-all duration-150 cursor-pointer ${isActive
                                    ? 'bg-[#7C3AED] text-white shadow-md shadow-purple-200'
                                    : 'text-[#111827] hover:bg-[#F3E8FF] hover:text-[#7C3AED] group'}`, children: [_jsx(Icon, { className: `w-4 h-4 transition-colors ${isActive ? 'text-white' : 'text-[#6B7280] group-hover:text-[#7C3AED]'}` }), _jsx("span", { children: item.name })] }, item.name));
                        }) })] }), _jsxs("div", { className: "p-4 border-t border-[#E5E7EB] bg-slate-50/50 flex items-center gap-3", children: [_jsx("div", { className: "w-9 h-9 rounded-full bg-[#F3E8FF] text-[#7C3AED] font-bold text-xs flex items-center justify-center", children: "AR" }), _jsxs("div", { children: [_jsx("h4", { className: "text-xs font-bold text-[#111827]", children: "Aarav R." }), _jsx("p", { className: "text-[10px] text-[#6B7280]", children: "Product Team" })] })] })] }));
};
