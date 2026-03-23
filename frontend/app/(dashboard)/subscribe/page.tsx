'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { Check, ShieldCheck, Loader2, CreditCard, Sparkles } from 'lucide-react';
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

export default function SubscribePage() {
    const { t } = useTranslation();
    const [selectedPlanId, setSelectedPlanId] = useState<number | null>(null);

    const { data: plans = [], isLoading } = useQuery({
        queryKey: ['billing-plans'],
        queryFn: async () => {
            const { data } = await apiClient.get('/billing/plans');
            // The API returns an array directly
            return (Array.isArray(data) ? data : data?.data || []) as Plan[];
        },
        retry: 1,
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

    if (isLoading) {
        return (
            <div className="flex h-[60vh] items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
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
