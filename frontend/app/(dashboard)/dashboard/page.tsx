'use client';

import { useQuery } from '@tanstack/react-query';
import {
    Users,
    MessageSquare,
    TrendingUp,
    UserCheck,
    Activity,
    CreditCard,
} from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import apiClient from '@/lib/api-client';
import type { DistributorMetrics, Channel } from '@/types';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

import { useTranslation } from 'react-i18next';

export default function DashboardPage() {
    const { t } = useTranslation();
    const { data: metrics, isLoading: loadingMetrics } = useQuery({
        queryKey: ['dashboard-metrics'],
        queryFn: async () => {
            const { data } = await apiClient.get<DistributorMetrics>('/dashboard/metrics');
            return data;
        },
    });

    const { data: channels, isLoading: loadingChannels } = useQuery({
        queryKey: ['channels'],
        queryFn: async () => {
            const { data } = await apiClient.get<{ data: Channel[] }>('/channels');
            return data.data;
        },
    });

    const cards = [
        {
            title: t('distributorDashboard.totalLeads'),
            value: metrics?.total_leads,
            icon: Users,
            description: t('distributorDashboard.allTime'),
        },
        {
            title: t('distributorDashboard.qualifiedLeads'),
            value: metrics?.qualified_leads,
            icon: UserCheck,
            description: t('distributorDashboard.readyForConversion'),
        },
        {
            title: t('distributorDashboard.messagesToday'),
            value: metrics?.messages_today,
            icon: MessageSquare,
            description: t('distributorDashboard.last24h'),
        },
        {
            title: t('distributorDashboard.conversionRate'),
            value: metrics?.conversion_rate !== undefined ? `${metrics.conversion_rate}%` : undefined,
            icon: TrendingUp,
            description: t('distributorDashboard.leadsToCustomers'),
        },
    ];

    return (
        <div className="space-y-8">
            <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold tracking-tight">{t('distributorDashboard.title')}</h2>
                <div className="flex items-center gap-2">
                    <Link href="/contacts">
                        <Button>{t('distributorDashboard.viewContacts')}</Button>
                    </Link>
                </div>
            </div>

            {/* Metrics Grid */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {cards.map((card, i) => (
                    <Card key={i}>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-sm font-medium">
                                {card.title}
                            </CardTitle>
                            <card.icon className="h-4 w-4 text-muted-foreground" />
                        </CardHeader>
                        <CardContent>
                            {loadingMetrics ? (
                                <Skeleton className="h-8 w-20" />
                            ) : (
                                <div className="text-2xl font-bold">{card.value ?? 0}</div>
                            )}
                            <p className="text-xs text-muted-foreground">
                                {card.description}
                            </p>
                        </CardContent>
                    </Card>
                ))}
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                {/* Channel Status */}
                <Card className="col-span-4">
                    <CardHeader>
                        <CardTitle>{t('distributorDashboard.communicationChannels')}</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {loadingChannels ? (
                            <div className="space-y-4">
                                <Skeleton className="h-12 w-full" />
                                <Skeleton className="h-12 w-full" />
                            </div>
                        ) : channels?.length === 0 ? (
                            <div className="flex flex-col items-center justify-center py-8 text-center text-muted-foreground">
                                <p className="mb-4">{t('distributorDashboard.noChannels')}</p>
                                <Link href="/channels">
                                    <Button variant="outline">{t('distributorDashboard.connectChannels')}</Button>
                                </Link>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {channels?.map((channel) => (
                                    <div key={channel.id} className="flex items-center justify-between rounded-lg border p-4">
                                        <div className="flex items-center gap-4">
                                            <div className={`flex h-10 w-10 items-center justify-center rounded-full ${channel.channel_type === 'whatsapp' ? 'bg-green-100 text-green-600' : 'bg-blue-100 text-blue-600'}`}>
                                                <Activity className="h-5 w-5" />
                                            </div>
                                            <div>
                                                <p className="font-medium capitalize">{channel.channel_type} - {channel.name}</p>
                                                <p className="text-sm text-muted-foreground capitalize">{t('common.status')}: {channel.status}</p>
                                            </div>
                                        </div>
                                        <div className={`h-2.5 w-2.5 rounded-full ${channel.status === 'active' ? 'bg-green-500' : 'bg-red-500'}`} />
                                    </div>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Recent Activity / Quick Actions Placeholder */}
                <Card className="col-span-3">
                    <CardHeader>
                        <CardTitle>{t('distributorDashboard.quickActions')}</CardTitle>
                    </CardHeader>
                    <CardContent className="grid gap-4">
                        <Link href="/agents/playground">
                            <Button variant="outline" className="w-full justify-start">
                                <MessageSquare className="mr-2 h-4 w-4" />
                                {t('distributorDashboard.testAgent')}
                            </Button>
                        </Link>
                        <Link href="/wellness">
                            <Button variant="outline" className="w-full justify-start">
                                <Activity className="mr-2 h-4 w-4" />
                                {t('distributorDashboard.wellnessEvaluations')}
                            </Button>
                        </Link>
                        <Link href="/subscribe">
                            <Button variant="outline" className="w-full justify-start">
                                <CreditCard className="mr-2 h-4 w-4" />
                                {t('distributorDashboard.manageSubscription')}
                            </Button>
                        </Link>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
