'use client';
import { jsx as _jsx } from "react/jsx-runtime";
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
export const QueryProvider = ({ children }) => {
    const [queryClient] = React.useState(() => new QueryClient({
        defaultOptions: {
            queries: {
                retry: 1,
                refetchOnWindowFocus: false,
            },
        },
    }));
    return (_jsx(QueryClientProvider, { client: queryClient, children: children }));
};
export default QueryProvider;
