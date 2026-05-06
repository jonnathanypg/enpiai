'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { 
    Check, 
    ShieldCheck, 
    Loader2, 
    CreditCard, 
    Sparkles, 
    Calendar, 
    Clock, 
    ArrowUpCircle, 
    XCircle,
    UserCheck,
    Zap
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import apiClient from '@/lib/api-client';
import { toast } from 'sonner';
import type { Plan } from '@/types';
import { cn } from '@/lib/utils';

interface MembershipInfo {
    status: string;
    is_active: boolean;
    plan_name?: string;
    plan_description?: string;
    price?: number;
    currency?: string;
    features?: Record<string, any>;
    start_date?: string;
    next_payment_at?: string;
    notes?: string;
}

export default function SubscribePage() {
    const { t } = useTranslation();
    const queryClient = useQueryClient();
    const [selectedPlanId, setSelectedPlanId] = useState<number | null>(null);
    const [showPlans, setShowPlans] = useState(false);

    // 1. Fetch Plans
    const { data: plans = [], isLoading: loadingPlans } = useQuery({
        queryKey: ['billing-plans'],
        queryFn: async () => {
            const { data } = await apiClient.get('/billing/plans');
            return (Array.isArray(data) ? data : data?.data || []) as Plan[];
        },
        retry: 1,
    });

    // 2. Fetch My Subscription
    const { data: membership, isLoading: loadingMembership } = useQuery<MembershipInfo>({
        queryKey: ['my-subscription'],
        queryFn: async () => {
            const { data } = await apiClient.get('/billing/my-subscription');
            return data;
        },
    });

    const subscribeMutation = useMutation({
        mutationFn: async (planId: number) => {
            const { data } = await apiClient.post('/billing/subscribe', {
                plan_id: planId,
            });
            return data;
        },
        onSuccess: (data) => {
            if (data.subscribe_url) {
                toast.success(t('subscribe.redirectingToGateway'));
                window.location.href = data.subscribe_url;
            } else {
                toast.error(t('subscribe.paymentUrlError'));
            }
        },
        onError: (error: any) => {
            toast.error(error?.response?.data?.error || t('subscribe.subscriptionError'));
        },
    });

    const handleSubscribe = (planId: number) => {
        setSelectedPlanId(planId);
        subscribeMutation.mutate(planId);
    };

    const isLoading = loadingPlans || loadingMembership;
    const hasActiveMembership = membership?.is_active && (
        membership.status === 'active' || 
        membership.status === 'courtesy' || 
        membership.status === 'trial' ||
        membership.status === 'pending'
    );

    if (isLoading) {
        return (
            <div className="flex h-[60vh] items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    // Render Membership View
    if (hasActiveMembership && membership) {
        return (
            <div className="mx-auto max-w-4xl space-y-8 py-8">
                {!showPlans ? (
                    <>
                        <div className="text-center space-y-3">
                            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-primary/10">
                                <UserCheck className="h-7 w-7 text-primary" />
                            </div>
                            <h1 className="text-4xl font-bold tracking-tight">
                                {t('subscribe.membership.title')}
                            </h1>
                            <p className="text-lg text-muted-foreground max-w-xl mx-auto">
                                {t('subscribe.membership.subtitle')}
                            </p>
                        </div>

                        <div className="grid gap-6 md:grid-cols-3">
                            {/* Main Membership Card */}
                            <Card className="md:col-span-2 border-2 border-primary/20 bg-gradient-to-br from-background to-primary/5">
                                <CardHeader className="pb-4">
                                    <div className="flex items-center justify-between">
                                        <Badge className={cn(
                                            "px-3 py-1 text-sm font-medium",
                                            membership.status === 'courtesy' ? "bg-amber-500/10 text-amber-500 border-amber-500/20" : "bg-primary/10 text-primary border-primary/20"
                                        )}>
                                            {membership.status === 'courtesy' ? t('subscribe.membership.courtesy') : t('subscribe.membership.active')}
                                        </Badge>
                                        {membership.next_payment_at && (
                                            <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                                                <Clock className="h-4 w-4" />
                                                {t('subscribe.membership.nextBilling')}: {new Date(membership.next_payment_at).toLocaleDateString()}
                                            </div>
                                        )}
                                    </div>
                                    <CardTitle className="text-3xl mt-4">
                                        {t(`planNames.${membership.plan_name}`, membership.plan_name || '')}
                                    </CardTitle>
                                    <CardDescription className="text-base">
                                        {t(`planDescriptions.${membership.plan_name}`, membership.plan_description || '')}
                                    </CardDescription>
                                </CardHeader>
                                <CardContent className="space-y-6">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="rounded-lg border bg-card p-4">
                                            <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">
                                                {t('subscribe.membership.startDate')}
                                            </div>
                                            <div className="flex items-center gap-2 font-semibold">
                                                <Calendar className="h-4 w-4 text-primary" />
                                                {membership.start_date ? new Date(membership.start_date).toLocaleDateString() : '-'}
                                            </div>
                                        </div>
                                        <div className="rounded-lg border bg-card p-4">
                                            <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">
                                                {t('subscribe.membership.status')}
                                            </div>
                                            <div className="flex items-center gap-2 font-semibold">
                                                <div className={cn("h-2 w-2 rounded-full", membership.is_active ? "bg-green-500" : "bg-red-500")} />
                                                {t(`subscribe.membership.${membership.status}`)}
                                            </div>
                                        </div>
                                    </div>

                                    {membership.features && (
                                        <div className="space-y-3">
                                            <h4 className="text-sm font-semibold flex items-center gap-2">
                                                <Zap className="h-4 w-4 text-primary" />
                                                {t('subscribe.membership.features')}
                                            </h4>
                                            <div className="grid grid-cols-2 gap-2">
                                                {Object.entries(membership.features).slice(0, 6).map(([key, value]) => (
                                                    <div key={key} className="flex items-center gap-2 text-sm text-muted-foreground">
                                                        <Check className="h-3 w-3 text-green-500" />
                                                        <span className="capitalize">{t(`planFeatures.${key.replace(/ /g, '_')}`, key.replace(/_/g, ' '))}: {typeof value === 'boolean' ? (value ? t('common.yes') : t('common.no')) : String(value)}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </CardContent>
                                <CardFooter className="bg-muted/30 pt-6 flex gap-4">
                                    <Button className="flex-1" variant="outline" onClick={() => setShowPlans(true)}>
                                        <ArrowUpCircle className="mr-2 h-4 w-4" />
                                        {t('subscribe.membership.upgrade')}
                                    </Button>
                                    {membership.status !== 'courtesy' && (
                                        <Button variant="ghost" className="text-destructive hover:text-destructive hover:bg-destructive/10">
                                            <XCircle className="mr-2 h-4 w-4" />
                                            {t('subscribe.membership.cancel')}
                                        </Button>
                                    )}
                                </CardFooter>
                            </Card>

                            {/* Security Sidebar */}
                            <div className="space-y-6">
                                <Card className="bg-primary/5 border-none">
                                    <CardHeader>
                                        <CardTitle className="text-sm">{t('subscribe.securePaymentTitle')}</CardTitle>
                                    </CardHeader>
                                    <CardContent className="text-xs text-muted-foreground leading-relaxed">
                                        {t('subscribe.securePaymentDescription')}
                                    </CardContent>
                                </Card>
                                <div className="p-4 rounded-xl border border-dashed text-center space-y-2">
                                    <ShieldCheck className="h-8 w-8 text-primary/40 mx-auto" />
                                    <p className="text-xs font-medium text-muted-foreground uppercase tracking-widest leading-tight">
                                        Secured by dLocal
                                    </p>
                                </div>
                            </div>
                        </div>
                    </>
                ) : (
                    <>
                        {/* Upgrade Plans View */}
                        <div className="text-center space-y-3">
                            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-primary/20 to-primary/5">
                                <Sparkles className="h-7 w-7 text-primary" />
                            </div>
                            <h1 className="text-4xl font-bold tracking-tight">
                                {t('subscribe.membership.upgrade')}
                            </h1>
                            <p className="text-lg text-muted-foreground max-w-xl mx-auto">
                                {t('subscribe.subtitle')}
                            </p>
                        </div>

                        <Button
                            variant="ghost"
                            onClick={() => setShowPlans(false)}
                            className="mb-2"
                        >
                            <ArrowUpCircle className="mr-2 h-4 w-4 rotate-[270deg]" />
                            {t('subscribe.membership.backToMembership')}
                        </Button>

                        {plans.length > 0 ? (
                            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                                {plans.map((plan) => (
                                    <Card
                                        key={plan.id}
                                        className="flex flex-col relative overflow-hidden border-2 hover:border-primary/50 transition-colors"
                                    >
                                        {plan.is_default && (
                                            <Badge className="absolute top-3 right-3">{t('common.recommended')}</Badge>
                                        )}
                                        <CardHeader>
                                            <CardTitle className="text-xl">
                                                {t(`planNames.${plan.name}`, plan.name)}
                                            </CardTitle>
                                            <CardDescription>
                                                {t(`planDescriptions.${plan.name}`, plan.description || '')}
                                            </CardDescription>
                                        </CardHeader>
                                        <CardContent className="flex-1">
                                            <div className="mb-6 flex items-baseline gap-1">
                                                <span className="text-4xl font-bold">
                                                    ${plan.price_monthly}
                                                </span>
                                                <span className="text-sm text-muted-foreground">
                                                    {plan.currency} {t('common.perMonth')}
                                                </span>
                                            </div>
                                            {plan.features && (
                                                <ul className="space-y-2.5">
                                                    {Object.entries(plan.features).map(([key, value]) => (
                                                        <li key={key} className="flex items-center text-sm">
                                                            <Check className="mr-2 h-4 w-4 text-green-500 shrink-0" />
                                                            <span className="capitalize">
                                                                {t(`planFeatures.${key.replace(/ /g, '_')}`, key.replace(/_/g, ' '))}: {
                                                                    typeof value === 'boolean'
                                                                        ? t(`planFeatures.${value}`)
                                                                        : String(value)
                                                                }
                                                            </span>
                                                        </li>
                                                    ))}
                                                </ul>
                                            )}
                                        </CardContent>
                                        <CardFooter>
                                            <Button
                                                className="w-full"
                                                size="lg"
                                                onClick={() => handleSubscribe(plan.id)}
                                                disabled={subscribeMutation.isPending && selectedPlanId === plan.id}
                                            >
                                                {subscribeMutation.isPending && selectedPlanId === plan.id ? (
                                                    <>
                                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                                        {t('subscribe.redirecting')}
                                                    </>
                                                ) : (
                                                    <>
                                                        <CreditCard className="mr-2 h-4 w-4" />
                                                        {t('subscribe.subscribeButton')}
                                                    </>
                                                )}
                                            </Button>
                                        </CardFooter>
                                    </Card>
                                ))}
                            </div>
                        ) : (
                            <Card className="p-12 text-center">
                                <p className="text-muted-foreground text-lg">
                                    {t('subscribe.noPlans')}
                                </p>
                            </Card>
                        )}

                        {/* Security Footer */}
                        <Card className="bg-gradient-to-br from-primary/5 via-transparent to-transparent">
                            <CardContent className="flex flex-col items-center gap-6 p-8 md:flex-row md:items-start md:text-left">
                                <div className="rounded-full bg-primary/10 p-4 shrink-0">
                                    <ShieldCheck className="h-8 w-8 text-primary" />
                                </div>
                                <div className="space-y-2">
                                    <h3 className="text-lg font-semibold">{t('subscribe.securePaymentTitle')}</h3>
                                    <p className="text-muted-foreground">
                                        {t('subscribe.securePaymentDescription')}
                                    </p>
                                </div>
                            </CardContent>
                        </Card>
                    </>
                )}
            </div>
        );
    }

    return (
        <div className="mx-auto max-w-5xl space-y-8 py-8">
            {/* Header */}
            <div className="text-center space-y-3">
                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-primary/20 to-primary/5">
                    <Sparkles className="h-7 w-7 text-primary" />
                </div>
                <h1 className="text-4xl font-bold tracking-tight">
                    {t('subscribe.title')}
                </h1>
                <p className="text-lg text-muted-foreground max-w-xl mx-auto">
                    {t('subscribe.subtitle')}
                </p>
            </div>

            {/* Plans Grid */}
            {plans.length > 0 ? (
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                    {plans.map((plan) => (
                        <Card
                            key={plan.id}
                            className="flex flex-col relative overflow-hidden border-2 hover:border-primary/50 transition-colors"
                        >
                            {plan.is_default && (
                                <Badge className="absolute top-3 right-3">{t('common.recommended')}</Badge>
                            )}
                            <CardHeader>
                                <CardTitle className="text-xl">
                                    {t(`planNames.${plan.name}`, plan.name)}
                                </CardTitle>
                                <CardDescription>
                                    {t(`planDescriptions.${plan.name}`, plan.description || '')}
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="flex-1">
                                <div className="mb-6 flex items-baseline gap-1">
                                    <span className="text-4xl font-bold">
                                        ${plan.price_monthly}
                                    </span>
                                    <span className="text-sm text-muted-foreground">
                                        {plan.currency} {t('common.perMonth')}
                                    </span>
                                </div>
                                {plan.features && (
                                    <ul className="space-y-2.5">
                                        {Object.entries(plan.features).map(([key, value]) => (
                                            <li key={key} className="flex items-center text-sm">
                                                <Check className="mr-2 h-4 w-4 text-green-500 shrink-0" />
                                                <span className="capitalize">
                                                    {t(`planFeatures.${key.replace(/ /g, '_')}`, key.replace(/_/g, ' '))}: {
                                                        typeof value === 'boolean' 
                                                            ? t(`planFeatures.${value}`) 
                                                            : String(value)
                                                    }
                                                </span>
                                            </li>
                                        ))}
                                    </ul>
                                )}
                            </CardContent>
                            <CardFooter>
                                <Button
                                    className="w-full"
                                    size="lg"
                                    onClick={() => handleSubscribe(plan.id)}
                                    disabled={subscribeMutation.isPending && selectedPlanId === plan.id}
                                >
                                    {subscribeMutation.isPending && selectedPlanId === plan.id ? (
                                        <>
                                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                            {t('subscribe.redirecting')}
                                        </>
                                    ) : (
                                        <>
                                            <CreditCard className="mr-2 h-4 w-4" />
                                            {t('subscribe.subscribeButton')}
                                        </>
                                    )}
                                </Button>
                            </CardFooter>
                        </Card>
                    ))}
                </div>
            ) : (
                <Card className="p-12 text-center">
                    <p className="text-muted-foreground text-lg">
                        {t('subscribe.noPlans')}
                    </p>
                </Card>
            )}

            {/* Security Footer */}
            <Card className="bg-gradient-to-br from-primary/5 via-transparent to-transparent">
                <CardContent className="flex flex-col items-center gap-6 p-8 md:flex-row md:items-start md:text-left">
                    <div className="rounded-full bg-primary/10 p-4 shrink-0">
                        <ShieldCheck className="h-8 w-8 text-primary" />
                    </div>
                    <div className="space-y-2">
                        <h3 className="text-lg font-semibold">{t('subscribe.securePaymentTitle')}</h3>
                        <p className="text-muted-foreground">
                            {t('subscribe.securePaymentDescription')}
                        </p>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
