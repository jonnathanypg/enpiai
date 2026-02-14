'use client';

import { useQuery } from '@tanstack/react-query';
import { Check, ShieldCheck, Zap, Bot, Database } from 'lucide-react';
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
import type { Subscription } from '@/types';

export default function SubscriptionPage() {
    const { data: subscription, isLoading } = useQuery({
        queryKey: ['subscription'],
        queryFn: async () => {
            // Assuming we have this endpoint or use /me
            const { data } = await apiClient.get<any>('/auth/me'); // Using auth/me for now as it includes distributor details
            return data.data.distributor;
        },
    });

    const plans = [
        {
            name: 'Starter',
            price: '$0',
            description: 'For individuals just getting started.',
            features: ['1 AI Agent', '50 Wellness Evals/mo', 'Basic Analytics', 'Community Support'],
            current: subscription?.subscription_tier === 'free',
        },
        {
            name: 'Pro',
            price: '$29',
            period: '/month',
            description: 'Unlock the full potential of AI automation.',
            features: ['3 AI Agents', 'Unlimited Wellness Evals', 'WhatsApp & Telegram Integration', 'Advanced CRM', 'Priority Support'],
            current: subscription?.subscription_tier === 'pro' || subscription?.subscription_tier === 'standard',
            popular: true,
        },
        {
            name: 'Enterprise',
            price: 'Contact Us',
            description: 'For top leaders and organizations.',
            features: ['Unlimited Agents', 'Custom RAG Knowledge Base', 'Dedicated Account Manager', 'SLA', 'API Access'],
            current: subscription?.subscription_tier === 'enterprise',
        },
    ];

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Subscription</h2>
                    <p className="text-muted-foreground">
                        Manage your plan and billing details.
                    </p>
                </div>
            </div>

            <div className="grid gap-6 md:grid-cols-3">
                {plans.map((plan) => (
                    <Card
                        key={plan.name}
                        className={`flex flex-col ${plan.popular ? 'border-primary shadow-lg' : ''} ${plan.current ? 'bg-muted/50' : ''}`}
                    >
                        <CardHeader>
                            {plan.popular && (
                                <Badge className="w-fit mb-2">Most Popular</Badge>
                            )}
                            <CardTitle className="text-xl">{plan.name}</CardTitle>
                            <CardDescription>{plan.description}</CardDescription>
                        </CardHeader>
                        <CardContent className="flex-1">
                            <div className="mb-6 flex items-baseline">
                                <span className="text-3xl font-bold">{plan.price}</span>
                                {plan.period && <span className="text-sm text-muted-foreground">{plan.period}</span>}
                            </div>
                            <ul className="space-y-2">
                                {plan.features.map((feature) => (
                                    <li key={feature} className="flex items-center text-sm">
                                        <Check className="mr-2 h-4 w-4 text-green-500" />
                                        {feature}
                                    </li>
                                ))}
                            </ul>
                        </CardContent>
                        <CardFooter>
                            <Button
                                className="w-full"
                                variant={plan.current ? 'secondary' : plan.popular ? 'default' : 'outline'}
                                disabled={plan.current}
                            >
                                {plan.current ? 'Current Plan' : plan.name === 'Enterprise' ? 'Contact Sales' : 'Upgrade'}
                            </Button>
                        </CardFooter>
                    </Card>
                ))}
            </div>

            {/* Feature Highlight */}
            <Card className="bg-gradient-to-br from-primary/5 via-transparent to-transparent">
                <CardContent className="flex flex-col items-center gap-6 p-8 md:flex-row md:items-start md:text-left">
                    <div className="rounded-full bg-primary/10 p-4">
                        <ShieldCheck className="h-8 w-8 text-primary" />
                    </div>
                    <div className="space-y-2">
                        <h3 className="text-lg font-semibold">Secure & Sovereign</h3>
                        <p className="text-muted-foreground">
                            All plans include our commitment to data sovereignty. Your customer data is encrypted and yours to keep, regardless of your subscription status.
                        </p>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
