import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Sidebar } from '../components/Sidebar';
import { TopNavbar } from '../components/TopNavbar';
export const MainLayout = ({ children }) => {
    return (_jsxs("div", { className: "flex bg-slate-50/50 min-h-screen text-slate-600 antialiased font-sans", children: [_jsx(Sidebar, {}), _jsxs("div", { className: "flex-1 flex flex-col min-w-0", children: [_jsx(TopNavbar, {}), _jsx("main", { className: "flex-grow p-8 overflow-y-auto", children: children })] })] }));
};
export default MainLayout;
