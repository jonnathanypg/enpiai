'use client';

import { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { Sidebar } from '@/components/shared/sidebar';
import { Header } from '@/components/shared/header';
import { Sheet, SheetContent } from '@/components/ui/sheet';
import { useAuthStore } from '@/store/use-auth-store';
import { useQuery } from '@tanstack/react-query';
import apiClient from '@/lib/api-client';

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const [collapsed, setCollapsed] = useState(false);
    const [mobileOpen, setMobileOpen] = useState(false);
    const router = useRouter();
    const pathname = usePathname();
    const { user, isAuthenticated } = useAuthStore();

    // Fetch distributor data so we always have fresh billing status
    const { data: meData } = useQuery({
        queryKey: ['me'],
        queryFn: async () => {
            const { data } = await apiClient.get('/auth/me');
            return data.data;
        },
        enabled: isAuthenticated,
        staleTime: 60_000, // 1 min cache to avoid spamming
    });

    const distributor = meData?.distributor;
    const isLoadingMe = !meData && isAuthenticated;

    // ---- Paywall Guard ----
    const isSuperAdmin = user?.role === 'super_admin';
    const hasActiveSubscription = distributor?.subscription_active === true;
    const isCourtesy = distributor?.is_courtesy === true;
    const isPaywallRoute = pathname === '/subscribe' || pathname.startsWith('/subscribe/');
    
    // We consider it restricted only when data is loaded and they don't have access
    const isRestricted = !isLoadingMe && distributor && !isSuperAdmin && !hasActiveSubscription && !isCourtesy;

    useEffect(() => {
        if (isLoadingMe || !distributor) return; // Still loading
        if (isPaywallRoute) return; // Already on paywall

        if (isRestricted) {
            window.location.href = '/subscribe';
        }
    }, [isLoadingMe, distributor, pathname, isRestricted, isPaywallRoute]);

    // We cover the screen if we are waiting on the API, or if we are actively redirecting out.
    // This entirely prevents the "flash" of the dashboard.
    const isBlocking = (isLoadingMe || isRestricted) && !isPaywallRoute;

    return (
        <div className="flex h-screen overflow-hidden relative">
            {isBlocking && (
                <div className="absolute inset-0 z-50 flex items-center justify-center bg-background">
                    <div className="flex flex-col items-center gap-2">
                        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
                        <p className="text-sm text-muted-foreground">Verifying access...</p>
                    </div>
                </div>
            )}
            
            {/* Desktop Sidebar - Hidden if restricted so paywall takes full width */}
            {!isRestricted && (
                <div className="hidden lg:block">
                    <Sidebar
                        collapsed={collapsed}
                        onToggle={() => setCollapsed(!collapsed)}
                    />
                </div>
            )}

            {/* Mobile Sidebar (Sheet) */}
            <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
                <SheetContent side="left" className="w-64 p-0">
                    <Sidebar collapsed={false} onToggle={() => setMobileOpen(false)} />
                </SheetContent>
            </Sheet>

            {/* Main Content */}
            <div className="flex flex-1 flex-col overflow-hidden">
                <Header onMobileMenuToggle={() => setMobileOpen(true)} />
                <main className="flex-1 overflow-y-auto p-4 md:p-6">{children}</main>
            </div>
        </div>
    );
}
