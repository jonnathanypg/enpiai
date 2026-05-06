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

    return (
        <QueryClientProvider client={queryClient}>
            <NextThemesProvider
                attribute="class"
                defaultTheme="system"
                enableSystem
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
