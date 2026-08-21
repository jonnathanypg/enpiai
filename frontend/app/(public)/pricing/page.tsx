'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { 
    Check, 
    ShieldCheck, 
    Loader2, 
    CreditCard, 
    Sparkles, 
    Zap,
    Coins,
    ArrowRight
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
import { LanguageSwitcher } from '@/components/shared/language-switcher';
import { ThemeToggle } from '@/components/shared/theme-toggle';
import apiClient from '@/lib/api-client';
import type { Plan } from '@/types';

export default function PublicPricingPage() {
    const { t } = useTranslation();
    const router = useRouter();

    // Fetch Plans
    const { data: plans = [], isLoading } = useQuery({
        queryKey: ['public-billing-plans'],
        queryFn: async () => {
            const { data } = await apiClient.get('/billing/plans');
            return (Array.isArray(data) ? data : data?.data || []) as Plan[];
        },
        retry: 1,
    });

    const handleSelectPlan = (planId: number) => {
        // Since the user is public/guest, redirect them to registration with redirect param
        router.push(`/register?redirect=/subscribe&plan_id=${planId}`);
    };

    const subscriptionPlans = plans.filter(p => !p.is_credit_block);
    const creditPlans = plans.filter(p => p.is_credit_block);

    const renderPlans = (plansList: Plan[], title?: string) => (
        <div className="space-y-6">
            {title && <h2 className="text-2xl font-bold text-center">{title}</h2>}
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 justify-center">
                {plansList.map((plan) => (
                    <Card
                        key={plan.id}
                        className="flex flex-col relative overflow-hidden border-2 hover:border-primary/50 transition-all duration-300 hover:shadow-lg bg-card"
                    >
                        {plan.is_default && (
                            <Badge className="absolute top-3 right-3">{t('common.recommended')}</Badge>
                        )}
                        <CardHeader>
                            <CardTitle className="text-xl flex items-center justify-between">
                                {t(`planNames.${plan.name}`, plan.name)}
                                {plan.is_credit_block && <Coins className="h-5 w-5 text-amber-500" />}
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
                                    {plan.currency} {plan.is_credit_block ? '' : t('common.perMonth')}
                                </span>
                            </div>
                            {plan.features && !plan.is_credit_block && (
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
                            {plan.is_credit_block && (
                                <div className="p-3 rounded-lg bg-amber-500/5 border border-amber-500/20 text-sm flex items-center gap-2">
                                    <Zap className="h-4 w-4 text-amber-500" />
                                    <span>{plan.credits_granted} credits included</span>
                                </div>
                            )}
                        </CardContent>
                        <CardFooter>
                            <Button
                                className="w-full bg-gradient-to-r from-green-500 to-emerald-600 text-white shadow-md hover:shadow-lg transition-all duration-300 border-0"
                                size="lg"
                                onClick={() => handleSelectPlan(plan.id)}
                            >
                                <CreditCard className="mr-2 h-4 w-4" />
                                {plan.is_credit_block ? "Buy Credits" : t('subscribe.subscribeButton')}
                            </Button>
                        </CardFooter>
                    </Card>
                ))}
            </div>
        </div>
    );

    return (
        <div className="flex min-h-screen flex-col bg-background">
            {/* Header Navigation */}
            <header className="sticky top-0 z-50 border-b border-border bg-background">
                <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
                    <Link href="/" className="flex items-center">
                        <img src="/favicon-enpiai-ligth.png" alt="Enpi AI" className="h-8 w-auto object-contain dark:hidden" />
                        <img src="/favicon-enpiai-dark.png" alt="Enpi AI" className="h-8 w-auto object-contain hidden dark:block" />
                    </Link>

                    <nav className="hidden items-center gap-6 text-sm text-muted-foreground md:flex">
                        <Link href="/#features" className="transition-colors hover:text-foreground">
                            {t('home.nav.features')}
                        </Link>
                        <Link href="/#how-it-works" className="transition-colors hover:text-foreground">
                            {t('home.nav.howItWorks')}
                        </Link>
                        <Link href="/pricing" className="text-foreground font-semibold">
                            {t('home.nav.pricing')}
                        </Link>
                    </nav>

                    <div className="flex items-center gap-3">
                        <LanguageSwitcher />
                        <ThemeToggle />
                        <Link href="/login" className="hidden sm:block">
                            <Button variant="ghost" size="sm">
                                {t('home.hero.signIn')}
                            </Button>
                        </Link>
                        <Link href="/register">
                            <Button size="sm" className="bg-gradient-to-r from-green-500 to-emerald-600 text-white shadow-md shadow-green-500/25 hover:shadow-lg hover:shadow-green-500/30 transition-all border-0">
                                {t('auth.register')} <ArrowRight className="ml-1 h-4 w-4" />
                            </Button>
                        </Link>
                    </div>
                </div>
            </header>

            {/* Main pricing section */}
            <main className="flex-1 mx-auto w-full max-w-5xl px-4 py-16 space-y-16">
                {/* Title and Intro */}
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

                {isLoading ? (
                    <div className="flex h-[40vh] items-center justify-center">
                        <Loader2 className="h-8 w-8 animate-spin text-primary" />
                    </div>
                ) : (
                    <>
                        {/* Subscription Plans */}
                        {subscriptionPlans.length > 0 ? (
                            renderPlans(subscriptionPlans, "Subscription Plans")
                        ) : (
                            <Card className="p-12 text-center">
                                <p className="text-muted-foreground text-lg">
                                    {t('subscribe.noPlans')}
                                </p>
                            </Card>
                        )}

                        {/* Credit Blocks */}
                        {creditPlans.length > 0 && (
                            <div className="pt-8 border-t">
                                {renderPlans(creditPlans, "Buy Credit Blocks")}
                            </div>
                        )}
                    </>
                )}

                {/* Security Info */}
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
            </main>
        </div>
    );
}
