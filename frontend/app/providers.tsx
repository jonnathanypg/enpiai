'use client';

import * as React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider as NextThemesProvider } from 'next-themes';
import { Toaster } from 'sonner';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { useTranslation } from 'react-i18next';
import '@/lib/i18n'; // Initialize i18n globally

export function Providers({ children }: { children: React.ReactNode }) {
    const { i18n } = useTranslation();
    const [queryClient] = React.useState(
        () =>
            new QueryClient({
                defaultOptions: {
                    queries: {
                        staleTime: 60 * 1000,
                        refetchOnWindowFocus: false,
                    },
                },
            })
    );

    // Restore saved language after mount to avoid SSR hydration mismatch
    React.useEffect(() => {
        const savedLng = localStorage.getItem('i18nextLng');
        if (savedLng && savedLng !== i18n.language) {
            i18n.changeLanguage(savedLng);
        }
    }, [i18n]);

    // Handle dynamic chunk load errors and Server Action failures due to container restarts
    React.useEffect(() => {
        const handleError = (e: ErrorEvent) => {
            const errorMsg = e.message || '';
            const target = e.target as any;
            const src = target?.src || target?.href || '';
            
            if (
                errorMsg.includes('ChunkLoadError') || 
                errorMsg.includes('Failed to fetch dynamically imported module') ||
                errorMsg.includes('Failed to find Server Action') ||
                src.includes('.next/static/chunks/')
            ) {
                console.warn('Stale assets or Server Action error detected. Reloading page...');
                window.location.reload();
            }
        };

        const handleRejection = (e: PromiseRejectionEvent) => {
            const reason = e.reason?.message || '';
            if (
                reason.includes('ChunkLoadError') || 
                reason.includes('Failed to fetch dynamically imported module') ||
                reason.includes('Failed to find Server Action')
            ) {
                console.warn('Unhandled promise rejection (stale assets). Reloading page...');
                window.location.reload();
            }
        };

        window.addEventListener('error', handleError);
        window.addEventListener('unhandledrejection', handleRejection);

        return () => {
            window.removeEventListener('error', handleError);
            window.removeEventListener('unhandledrejection', handleRejection);
        };
    }, []);

    return (
        <QueryClientProvider client={queryClient}>
            <NextThemesProvider
                attribute="class"
                defaultTheme="dark"
                enableSystem={false}
                disableTransitionOnChange
            >
                <GoogleOAuthProvider clientId={process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || ''}>
                    {children}
                    <Toaster richColors position="top-right" />
                </GoogleOAuthProvider>
            </NextThemesProvider>
        </QueryClientProvider>
    );
}
