'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import {
    Users,
    CreditCard,
    MessageSquare,
    TrendingUp,
    Building2,
    Activity,
    ShieldCheck,
} from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';
import apiClient from '@/lib/api-client';
import { useAuthStore } from '@/store/use-auth-store';
import type { PlatformMetrics } from '@/types';

export default function AdminDashboardPage() {
    const router = useRouter();
    const { t } = useTranslation();
    const user = useAuthStore((s) => s.user);

    // Guard: Only super_admin can access
    useEffect(() => {
        if (user && user.role !== 'super_admin') {
            router.replace('/dashboard');
        }
    }, [user, router]);

    const { data: metrics, isLoading } = useQuery({
        queryKey: ['admin-platform-metrics'],
        queryFn: async () => {
            const { data } = await apiClient.get<{ data: PlatformMetrics }>('/admin/metrics');
            return data.data;
        },
        enabled: user?.role === 'super_admin',
    });

    if (user?.role !== 'super_admin') {
        return (
            <div className="flex h-[50vh] items-center justify-center">
                <p className="text-lg text-muted-foreground">{t('common.accessDenied')}</p>
            </div>
        );
    }

    const cards = [
        {
            title: t('adminDashboard.totalDistributors'),
            value: metrics?.total_distributors,
            icon: Building2,
            description: t('adminDashboard.distributorsDesc'),
            color: 'text-blue-500',
        },
        {
            title: t('adminDashboard.activeSubscriptions'),
            value: metrics?.active_subscriptions,
            icon: CreditCard,
            description: t('adminDashboard.subscriptionsDesc'),
            color: 'text-green-500',
        },
        {
            title: t('adminDashboard.mrr'),
            value: metrics?.mrr !== undefined ? `$${metrics.mrr.toFixed(2)}` : undefined,
            icon: TrendingUp,
            description: t('adminDashboard.mrrDesc'),
            color: 'text-emerald-500',
        },
        {
            title: t('adminDashboard.totalLeads'),
            value: metrics?.total_leads,
            icon: Users,
            description: t('adminDashboard.leadsDesc'),
            color: 'text-orange-500',
        },
        {
            title: t('adminDashboard.totalCustomers'),
            value: metrics?.total_customers,
            icon: Users,
            description: t('adminDashboard.customersDesc'),
            color: 'text-violet-500',
        },
        {
            title: t('adminDashboard.totalConversations'),
            value: metrics?.total_conversations,
            icon: MessageSquare,
            description: t('adminDashboard.conversationsDesc'),
            color: 'text-cyan-500',
        },
        {
            title: t('adminDashboard.totalMessages'),
            value: metrics?.total_messages,
            icon: Activity,
            description: t('adminDashboard.messagesDesc'),
            color: 'text-pink-500',
        },
    ];

    return (
        <div className="space-y-8">
            <div>
                <h2 className="flex items-center gap-2 text-3xl font-bold tracking-tight">
                    <ShieldCheck className="h-7 w-7 text-primary" />
                    {t('adminDashboard.title')}
                </h2>
                <p className="text-muted-foreground">
                    {t('adminDashboard.description')}
                </p>
            </div>

            <Separator />

            {/* Metrics Grid */}
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {cards.map((card, i) => (
                    <Card key={i}>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">{card.title}</CardTitle>
                            <card.icon className={`h-5 w-5 ${card.color}`} />
                        </CardHeader>
                        <CardContent>
                            {isLoading ? (
                                <Skeleton className="h-8 w-24" />
                            ) : (
                                <div className="text-2xl font-bold">{card.value ?? 0}</div>
                            )}
                            <p className="text-xs text-muted-foreground">{card.description}</p>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {/* System Info */}
            <Card>
                <CardHeader>
                    <CardTitle className="text-sm font-medium">{t('adminDashboard.systemInfo')}</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid gap-4 md:grid-cols-3">
                        <div className="rounded-lg border p-4">
                            <p className="text-sm font-medium text-muted-foreground">Backend</p>
                            <p className="text-lg font-bold">Flask + LangGraph</p>
                        </div>
                        <div className="rounded-lg border p-4">
                            <p className="text-sm font-medium text-muted-foreground">Vector DB</p>
                            <p className="text-lg font-bold">Pinecone</p>
                        </div>
                        <div className="rounded-lg border p-4">
                            <p className="text-sm font-medium text-muted-foreground">Queue</p>
                            <p className="text-lg font-bold">Redis + Celery</p>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
