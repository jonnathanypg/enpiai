'use client';

import { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { Sidebar } from '@/components/shared/sidebar';
import { Header } from '@/components/shared/header';
import { Sheet, SheetContent } from '@/components/ui/sheet';
import { useAuthStore } from '@/store/use-auth-store';
import { useQuery } from '@tanstack/react-query';
import apiClient from '@/lib/api-client';
import { useTranslation } from 'react-i18next';
import { OnboardingWelcomeModal } from '@/components/shared/onboarding-welcome-modal';
import { OnboardingTour } from '@/components/shared/onboarding-tour';
import { OnboardingChecklistWidget } from '@/components/shared/onboarding-checklist-widget';
import { useOnboardingStore } from '@/store/use-onboarding-store';

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const { t } = useTranslation();
    const [collapsed, setCollapsed] = useState(false);
    const [mobileOpen, setMobileOpen] = useState(false);
    const router = useRouter();
    const pathname = usePathname();
    const { user, isAuthenticated, hydrated } = useAuthStore();
    const onboarding = useOnboardingStore();

    // Reset onboarding progress if the logged-in user changes (avoid cross-session state persistence in localStorage)
    useEffect(() => {
        if (user?.id) {
            const storedUserId = localStorage.getItem('enpiai-onboarding-user-id');
            if (storedUserId !== String(user.id)) {
                onboarding.reset();
                localStorage.setItem('enpiai-onboarding-user-id', String(user.id));
            }
        } else {
            localStorage.removeItem('enpiai-onboarding-user-id');
        }
    }, [user?.id, onboarding]);

    // Fetch distributor data so we always have fresh billing status
    const { data: meData } = useQuery({
        queryKey: ['me'],
        queryFn: async () => {
            const { data } = await apiClient.get('/auth/me');
            return data.data;
        },
        enabled: isAuthenticated && hydrated,
        staleTime: 60_000, // 1 min cache to avoid spamming
    });

    const distributor = meData?.distributor;
    const isLoadingMe = !meData && isAuthenticated;

    // ---- Paywall Guard ----
    const isSuperAdmin = user?.role === 'super_admin';
    const hasActiveSubscription = distributor?.subscription_active === true;
    const isCourtesy = distributor?.is_courtesy === true;
    const isPaywallRoute = pathname === '/subscribe' || pathname.startsWith('/subscribe/') || pathname === '/activate-trial' || pathname === '/feedback';
    
    // We consider it restricted only when data is loaded and they don't have access
    const isRestricted = hydrated && !isLoadingMe && distributor && !isSuperAdmin && !hasActiveSubscription && !isCourtesy;

    const showTrialBanner = distributor?.is_in_trial === true && !isPaywallRoute;
    const [hoursRemaining, setHoursRemaining] = useState<number>(24);

    useEffect(() => {
        if (!distributor?.created_at) return;
        const updateTimer = () => {
            let dateStr = distributor.created_at;
            if (dateStr && !dateStr.endsWith('Z') && !dateStr.includes('+') && !dateStr.includes('-')) {
                dateStr = dateStr + 'Z';
            }
            const diffMs = (new Date(dateStr).getTime() + 24 * 60 * 60 * 1000) - Date.now();
            const hours = Math.max(0, Math.ceil(diffMs / (1000 * 60 * 60)));
            setHoursRemaining(hours);
        };
        updateTimer();
        const interval = setInterval(updateTimer, 60_000);
        return () => clearInterval(interval);
    }, [distributor?.created_at]);

    useEffect(() => {
        if (!isAuthenticated) return; // Unauthenticated users should be handled by middleware, bypass redirects
        if (!hydrated || isLoadingMe || !distributor) return; // Still loading
        if (isSuperAdmin) return; // Super admins bypass all paywall / trial redirects
        if (isPaywallRoute) return; // Already on paywall/special page

        // 1. If trial not activated yet
        if (distributor.trial_activated === false) {
            if (pathname !== '/activate-trial') {
                window.location.href = '/activate-trial';
            }
            return;
        }

        // If trial is activated, but user is on /activate-trial, redirect to dashboard
        if (distributor.trial_activated === true && pathname === '/activate-trial') {
            router.push('/dashboard');
            return;
        }

        // 2. If expired and feedback not submitted yet
        if (!hasActiveSubscription && !isCourtesy && distributor.feedback_submitted === false) {
            window.location.href = '/feedback';
            return;
        }

        // 3. Otherwise if restricted
        if (isRestricted) {
            window.location.href = '/subscribe';
        }
    }, [hydrated, isLoadingMe, distributor, pathname, isRestricted, isPaywallRoute, hasActiveSubscription, isCourtesy]);

    // Close mobile navigation drawer on route change
    useEffect(() => {
        setMobileOpen(false);
    }, [pathname]);

    // We cover the screen if we are waiting on the API, or if we are actively redirecting out.
    // This entirely prevents the "flash" of the dashboard.
    const isBlocking = (!hydrated || isLoadingMe || isRestricted) && !isPaywallRoute;

    const hasDashboardAccess = isSuperAdmin || hasActiveSubscription || isCourtesy;

    return (
        <div className="flex h-screen overflow-hidden relative">
            {isBlocking && (
                <div className="absolute inset-0 z-50 flex items-center justify-center bg-background">
                    <div className="flex flex-col items-center gap-2">
                        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
                        <p className="text-sm text-muted-foreground">{t('common.verifyingAccess')}</p>
                    </div>
                </div>
            )}
            
            {/* Desktop Sidebar - Hidden if restricted so paywall takes full width */}
            {!isRestricted && (
                <div className="hidden lg:block relative z-[45]">
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
                {showTrialBanner && (
                    <div className="bg-gradient-to-r from-indigo-600/90 to-violet-600/90 text-white py-2 px-4 text-center text-xs font-semibold flex items-center justify-center gap-1 relative z-30 shadow-sm">
                        <span className="flex items-center gap-1.5">
                            <span className="animate-pulse inline-block h-2 w-2 rounded-full bg-green-400" />
                            {t('subscribe.membership.trialBannerText', { hours: hoursRemaining })}
                        </span>
                        <button 
                            className="underline hover:text-indigo-200 transition-colors font-bold ml-2 focus:outline-none"
                            onClick={() => router.push('/subscribe')}
                        >
                            {t('subscribe.membership.trialBannerAction')} &rarr;
                        </button>
                    </div>
                )}
                <main className="flex-1 overflow-y-auto p-4 md:p-6">{children}</main>
            </div>

            {/* Onboarding System - Only if they have dashboard access, are not Super Admin, and are not being redirected */}
            {isAuthenticated && hasDashboardAccess && !isSuperAdmin && !isBlocking && !isPaywallRoute && (
                <>
                    <OnboardingWelcomeModal />
                    <OnboardingTour />
                    <OnboardingChecklistWidget />
                </>
            )}
        </div>
    );
}
