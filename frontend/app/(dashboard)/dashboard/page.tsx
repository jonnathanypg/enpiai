'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
    Users,
    MessageSquare,
    TrendingUp,
    UserCheck,
    Activity,
    CreditCard,
    Bot,
    Sparkles,
    Calendar,
    Radio,
    Copy,
    ExternalLink,
    Check,
    FileText,
    ArrowRight,
    Flame,
    Share2,
    ShieldAlert
} from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import apiClient from '@/lib/api-client';
import type { DistributorMetrics, Channel, WellnessEvaluation } from '@/types';
import { Button } from '@/components/ui/button';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import Link from 'next/link';
import { useTranslation } from 'react-i18next';
import { toast } from 'sonner';
import { useAuthStore } from '@/store/use-auth-store';
import { OnboardingDashboardBanner } from '@/components/shared/onboarding-dashboard-banner';

export default function DashboardPage() {
    const { t, i18n } = useTranslation();
    const [period, setPeriod] = useState('30');
    const user = useAuthStore((s) => s.user) as any;

    const distributorId = user?.distributor?.herbalife_id
        || user?.distributor?.id
        || user?.distributor_id
        || '';

    // 1. Fetch metrics
    const { data: metrics, isLoading: loadingMetrics } = useQuery({
        queryKey: ['dashboard-metrics', period],
        queryFn: async () => {
            const { data } = await apiClient.get<DistributorMetrics>('/dashboard/metrics');
            return data;
        },
        staleTime: 30 * 1000,
    });

    // 2. Fetch channels
    const { data: channels, isLoading: loadingChannels } = useQuery({
        queryKey: ['channels'],
        queryFn: async () => {
            const { data } = await apiClient.get<{ data: Channel[] }>('/channels');
            return data.data;
        },
        staleTime: 30 * 1000,
    });

    // 3. Fetch recent wellness evaluations for quick dashboard preview
    const { data: recentEvaluations, isLoading: loadingEvaluations } = useQuery({
        queryKey: ['dashboard-recent-evaluations'],
        queryFn: async () => {
            const { data } = await apiClient.get<{ data: WellnessEvaluation[] }>('/wellness/evaluations?per_page=5');
            return data.data;
        },
        staleTime: 30 * 1000,
    });

    const shareUrl = typeof window !== 'undefined' && distributorId
        ? `${window.location.origin}/evaluate/${distributorId}`
        : 'https://enpi.click/evaluate/' + distributorId;

    const copyLink = () => {
        if (!distributorId) {
            toast.error(t('common.error', { defaultValue: 'ID de distribuidor no disponible. Configúralo en Perfil.' }));
            return;
        }
        navigator.clipboard.writeText(shareUrl);
        toast.success(t('wellness.copySuccess', { defaultValue: '¡Link de Evaluación copiado al portapapeles!' }));
    };

    const cards = [
        {
            title: t('distributorDashboard.totalLeads', { defaultValue: 'Prospectos Totales' }),
            value: metrics?.total_leads,
            icon: Users,
            iconColor: 'text-blue-500 bg-blue-500/10 border-blue-500/20',
            description: t('distributorDashboard.allTime', { defaultValue: 'Base de contactos activa' }),
        },
        {
            title: t('distributorDashboard.qualifiedLeads', { defaultValue: 'Prospectos Calificados' }),
            value: metrics?.qualified_leads,
            icon: UserCheck,
            iconColor: 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20',
            description: t('distributorDashboard.readyForConversion', { defaultValue: 'Alta intención de compra' }),
        },
        {
            title: t('distributorDashboard.wellnessEvaluations', { defaultValue: 'Encuestas de Bienestar' }),
            value: metrics?.total_evaluations ?? recentEvaluations?.length,
            icon: Activity,
            iconColor: 'text-teal-500 bg-teal-500/10 border-teal-500/20',
            description: 'Diagnósticos generados con IA',
        },
        {
            title: t('distributorDashboard.messagesToday', { defaultValue: 'Mensajes Hoy' }),
            value: metrics?.messages_today,
            icon: MessageSquare,
            iconColor: 'text-amber-500 bg-amber-500/10 border-amber-500/20',
            description: t('distributorDashboard.last24h', { defaultValue: 'Atención automatizada 24/7' }),
        },
        {
            title: t('distributorDashboard.conversionRate', { defaultValue: 'Tasa de Conversión' }),
            value: metrics?.conversion_rate !== undefined ? `${metrics.conversion_rate}%` : '0%',
            icon: TrendingUp,
            iconColor: 'text-purple-500 bg-purple-500/10 border-purple-500/20',
            description: t('distributorDashboard.leadsToCustomers', { defaultValue: 'Prospectos a Clientes' }),
        },
    ];

    // Pipeline stages for Funnel
    const pipelineData = [
        { label: 'Nuevos Prospectos', count: metrics?.pipeline?.new ?? metrics?.total_leads ?? 0, color: 'bg-blue-500' },
        { label: 'Encuestas de Bienestar', count: metrics?.total_evaluations ?? recentEvaluations?.length ?? 0, color: 'bg-teal-500' },
        { label: 'Prospectos Calificados', count: metrics?.qualified_leads ?? 0, color: 'bg-emerald-500' },
        { label: 'En Seguimiento Nutricional', count: metrics?.pipeline?.nurturing ?? 0, color: 'bg-amber-500' },
        { label: 'Clientes Convertidos', count: metrics?.total_customers ?? metrics?.pipeline?.converted ?? 0, color: 'bg-purple-500' },
    ];

    const maxPipelineCount = Math.max(...pipelineData.map(p => p.count), 1);

    return (
        <div className="space-y-8 pb-10">
            {/* Onboarding Activation Banner */}
            <OnboardingDashboardBanner />
            
            {/* Dashboard Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-3xl font-extrabold tracking-tight text-foreground">
                        {t('distributorDashboard.title', { defaultValue: 'Panel del Distribuidor' })}
                    </h2>
                    <p className="text-sm text-muted-foreground mt-0.5">
                        Centro de control de prospección con IA, canales y evaluaciones nutricionales.
                    </p>
                </div>
                <div className="flex flex-wrap items-center gap-2.5">
                    <Tabs value={period} onValueChange={setPeriod}>
                        <TabsList className="bg-muted/60 p-1 rounded-xl">
                            <TabsTrigger value="7" className="rounded-lg text-xs">7D</TabsTrigger>
                            <TabsTrigger value="30" className="rounded-lg text-xs">30D</TabsTrigger>
                            <TabsTrigger value="90" className="rounded-lg text-xs">90D</TabsTrigger>
                            <TabsTrigger value="365" className="rounded-lg text-xs">1A</TabsTrigger>
                        </TabsList>
                    </Tabs>
                    <Link href="/contacts">
                        <Button variant="outline" className="rounded-xl text-xs font-semibold">
                            <Users className="mr-1.5 h-3.5 w-3.5" /> {t('distributorDashboard.viewContacts', { defaultValue: 'Ver Contactos' })}
                        </Button>
                    </Link>
                </div>
            </div>

            {/* Metrics Grid (5 Columns) */}
            <div className="grid gap-4 grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
                {cards.map((card, i) => (
                    <Card key={i} className="rounded-2xl border-border/70 shadow-sm hover:shadow-md transition-shadow">
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <CardTitle className="text-xs font-bold text-muted-foreground">
                                {card.title}
                            </CardTitle>
                            <div className={`p-2 rounded-xl border ${card.iconColor}`}>
                                <card.icon className="h-4 w-4" />
                            </div>
                        </CardHeader>
                        <CardContent>
                            {loadingMetrics ? (
                                <Skeleton className="h-8 w-20 rounded-lg" />
                            ) : (
                                <div className="text-2xl font-black text-foreground">{card.value ?? 0}</div>
                            )}
                            <p className="text-[11px] text-muted-foreground mt-1 truncate">
                                {card.description}
                            </p>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {/* Main Sections: Funnel + Quick Action Hub */}
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-7">
                {/* Sales & Wellness Funnel (Spans 4 columns) */}
                <Card className="col-span-4 rounded-3xl border-border/70 shadow-sm flex flex-col justify-between">
                    <CardHeader>
                        <div className="flex items-center justify-between">
                            <div>
                                <CardTitle className="text-lg font-bold flex items-center gap-2">
                                    <TrendingUp className="w-5 h-5 text-emerald-500" />
                                    Embudo de Prospección y Conversión
                                </CardTitle>
                                <CardDescription className="text-xs">
                                    Flujo de nutrición y calificación de prospectos a clientes
                                </CardDescription>
                            </div>
                            <Link href="/contacts">
                                <Button variant="ghost" size="sm" className="text-xs rounded-xl">
                                    Ver CRM <ArrowRight className="ml-1 h-3.5 w-3.5" />
                                </Button>
                            </Link>
                        </div>
                    </CardHeader>
                    <CardContent className="space-y-4 py-2">
                        {loadingMetrics ? (
                            <div className="space-y-4">
                                <Skeleton className="h-8 w-full rounded-xl" />
                                <Skeleton className="h-8 w-4/5 rounded-xl" />
                                <Skeleton className="h-8 w-3/5 rounded-xl" />
                                <Skeleton className="h-8 w-2/5 rounded-xl" />
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {pipelineData.map((item, index) => {
                                    const percentage = Math.max(8, Math.round((item.count / maxPipelineCount) * 100));
                                    return (
                                        <div key={index} className="space-y-1">
                                            <div className="flex justify-between text-xs font-semibold">
                                                <span className="text-foreground">{item.label}</span>
                                                <span className="text-muted-foreground">{item.count} contactos</span>
                                            </div>
                                            <div className="w-full bg-muted/60 rounded-full h-3 overflow-hidden p-0.5 border border-border/40">
                                                <div 
                                                    className={`h-full rounded-full transition-all duration-700 ease-out ${item.color}`}
                                                    style={{ width: `${percentage}%` }}
                                                />
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </CardContent>
                    <div className="p-4 mx-6 mb-6 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-between text-xs">
                        <span className="text-emerald-950 dark:text-emerald-300 font-semibold">
                            💡 Tip: Comparte tu link de chequeo de bienestar para aumentar tu flujo de prospectos calificados.
                        </span>
                    </div>
                </Card>

                {/* Quick Actions & Viral Share Hub (Spans 3 columns) */}
                <Card className="col-span-3 rounded-3xl border-border/70 shadow-sm flex flex-col justify-between">
                    <CardHeader>
                        <CardTitle className="text-lg font-bold flex items-center gap-2">
                            <Sparkles className="w-5 h-5 text-amber-500" />
                            Centro de Prospección Rápida
                        </CardTitle>
                        <CardDescription className="text-xs">
                            Herramientas clave para captar y atender prospectos hoy
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {/* 1-Click Wellness Link Box */}
                        <div className="p-4 rounded-2xl bg-gradient-to-br from-emerald-500/10 via-teal-500/10 to-slate-900/10 border border-emerald-500/25 space-y-2.5">
                            <div className="flex items-center justify-between">
                                <span className="text-xs font-bold text-emerald-800 dark:text-emerald-300 flex items-center gap-1.5">
                                    🌿 Link de Chequeo de Bienestar
                                </span>
                                <Badge variant="outline" className="text-[10px] bg-background border-emerald-500/30 text-emerald-600 dark:text-emerald-400 font-bold">
                                    Público
                                </Badge>
                            </div>
                            <p className="text-[11px] text-muted-foreground leading-relaxed">
                                Envía este link por WhatsApp a tus prospectos. La IA los diagnosticará y los guardará en tu CRM.
                            </p>
                            <div className="flex gap-2 pt-1">
                                <Button 
                                    size="sm" 
                                    onClick={copyLink} 
                                    className="flex-1 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-md shadow-emerald-600/20"
                                >
                                    <Copy className="mr-1.5 h-3.5 w-3.5" /> Copiar Link
                                </Button>
                                <Button 
                                    size="sm" 
                                    variant="outline" 
                                    onClick={() => distributorId && window.open(`/evaluate/${distributorId}`, '_blank')}
                                    className="rounded-xl text-xs"
                                >
                                    <ExternalLink className="h-3.5 w-3.5" />
                                </Button>
                            </div>
                        </div>

                        {/* Quick Navigation Links */}
                        <div className="grid gap-2 text-xs">
                            <Link href="/agents/playground">
                                <Button variant="outline" className="w-full justify-start rounded-xl text-xs h-11 border-border/70 hover:bg-muted/60">
                                    <Bot className="mr-2.5 h-4 w-4 text-indigo-500" />
                                    {t('distributorDashboard.testAgent', { defaultValue: 'Chatear con Asistente / Playground' })}
                                </Button>
                            </Link>
                            <Link href="/coach">
                                <Button variant="outline" className="w-full justify-start rounded-xl text-xs h-11 border-border/70 hover:bg-muted/60">
                                    <Sparkles className="mr-2.5 h-4 w-4 text-purple-500" />
                                    Modo Coach Nutricional IA
                                </Button>
                            </Link>
                            <Link href="/wellness">
                                <Button variant="outline" className="w-full justify-start rounded-xl text-xs h-11 border-border/70 hover:bg-muted/60">
                                    <Activity className="mr-2.5 h-4 w-4 text-teal-500" />
                                    Gestionar Evaluaciones y Reportes PDF
                                </Button>
                            </Link>
                            <Link href="/subscribe">
                                <Button variant="outline" className="w-full justify-start rounded-xl text-xs h-11 border-border/70 hover:bg-muted/60">
                                    <CreditCard className="mr-2.5 h-4 w-4 text-emerald-500" />
                                    {t('distributorDashboard.manageSubscription', { defaultValue: 'Membresía y Licencia Herbalife' })}
                                </Button>
                            </Link>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Bottom Row: Communication Channels + Recent Wellness Evaluations */}
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-7">
                {/* Communication Channels (Spans 3 columns) */}
                <Card className="col-span-3 rounded-3xl border-border/70 shadow-sm">
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                        <div>
                            <CardTitle className="text-base font-bold flex items-center gap-2">
                                <Radio className="w-4 h-4 text-green-500" />
                                {t('distributorDashboard.communicationChannels', { defaultValue: 'Canales de Comunicación' })}
                            </CardTitle>
                            <CardDescription className="text-xs">Estado de conexión con WhatsApp y redes</CardDescription>
                        </div>
                        <Link href="/channels">
                            <Button variant="ghost" size="sm" className="text-xs rounded-xl">Configurar</Button>
                        </Link>
                    </CardHeader>
                    <CardContent className="pt-3">
                        {loadingChannels ? (
                            <div className="space-y-3">
                                <Skeleton className="h-14 w-full rounded-2xl" />
                                <Skeleton className="h-14 w-full rounded-2xl" />
                            </div>
                        ) : !channels || channels.length === 0 ? (
                            <div className="flex flex-col items-center justify-center py-6 text-center text-muted-foreground space-y-3">
                                <p className="text-xs">No tienes canales conectados aún.</p>
                                <Link href="/channels">
                                    <Button size="sm" className="rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold">
                                        Conectar WhatsApp
                                    </Button>
                                </Link>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {channels.map((channel) => (
                                    <div key={channel.id} className="flex items-center justify-between rounded-2xl border border-border/60 p-3.5 bg-muted/20">
                                        <div className="flex items-center gap-3">
                                            <div className={`flex h-9 w-9 items-center justify-center rounded-xl font-bold text-sm ${
                                                channel.channel_type === 'whatsapp' 
                                                    ? 'bg-green-500/15 text-green-600 dark:text-green-400' 
                                                    : 'bg-blue-500/15 text-blue-600 dark:text-blue-400'
                                            }`}>
                                                {channel.channel_type === 'whatsapp' ? '📱' : '💬'}
                                            </div>
                                            <div>
                                                <p className="font-bold text-xs capitalize text-foreground">{channel.channel_type} - {channel.name}</p>
                                                <p className="text-[11px] text-muted-foreground capitalize">Estado: {channel.status}</p>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <span className={`h-2.5 w-2.5 rounded-full ${channel.status === 'active' ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
                                            <Badge variant={channel.status === 'active' ? 'default' : 'destructive'} className="text-[10px] rounded-lg">
                                                {channel.status === 'active' ? 'Conectado' : 'Inactivo'}
                                            </Badge>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Recent Wellness Evaluations (Spans 4 columns) */}
                <Card className="col-span-4 rounded-3xl border-border/70 shadow-sm">
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                        <div>
                            <CardTitle className="text-base font-bold flex items-center gap-2">
                                <Activity className="w-4 h-4 text-teal-500" />
                                Evaluaciones de Bienestar Recientes
                            </CardTitle>
                            <CardDescription className="text-xs">Últimos diagnósticos completados por prospectos</CardDescription>
                        </div>
                        <Link href="/wellness">
                            <Button variant="ghost" size="sm" className="text-xs rounded-xl">
                                Ver Todas <ArrowRight className="ml-1 h-3.5 w-3.5" />
                            </Button>
                        </Link>
                    </CardHeader>
                    <CardContent className="pt-3">
                        {loadingEvaluations ? (
                            <div className="space-y-3">
                                <Skeleton className="h-12 w-full rounded-2xl" />
                                <Skeleton className="h-12 w-full rounded-2xl" />
                                <Skeleton className="h-12 w-full rounded-2xl" />
                            </div>
                        ) : !recentEvaluations || recentEvaluations.length === 0 ? (
                            <div className="flex flex-col items-center justify-center py-6 text-center text-muted-foreground space-y-3">
                                <p className="text-xs">Aún no se han recibido evaluaciones de bienestar.</p>
                                <Button size="sm" variant="outline" onClick={copyLink} className="rounded-xl text-xs">
                                    <Copy className="mr-1.5 h-3.5 w-3.5" /> Copiar Link para Prospectos
                                </Button>
                            </div>
                        ) : (
                            <div className="space-y-2.5">
                                {recentEvaluations.map((ev) => (
                                    <div key={ev.id} className="flex items-center justify-between rounded-2xl border border-border/50 p-3 bg-muted/20 hover:bg-muted/40 transition-colors">
                                        <div className="space-y-0.5">
                                            <Link 
                                                href={`/contacts/${ev.lead_id ? 'lead:' + ev.lead_id : 'customer:' + ev.customer_id}`}
                                                className="font-bold text-xs text-foreground hover:underline flex items-center gap-1.5"
                                            >
                                                {(ev as any).contact_name || `Evaluación #${ev.id}`}
                                            </Link>
                                            <p className="text-[11px] text-muted-foreground truncate max-w-xs">
                                                Meta: {ev.primary_goal || 'Bienestar General'}
                                            </p>
                                        </div>
                                        <div className="flex items-center gap-2.5">
                                            <Badge variant={ev.bmi && ev.bmi > 25 ? 'destructive' : 'outline'} className="text-[10px] rounded-lg">
                                                IMC: {ev.bmi ? ev.bmi.toFixed(1) : 'N/A'}
                                            </Badge>
                                            {ev.pdf_report_path && (
                                                <Button 
                                                    size="sm" 
                                                    variant="ghost" 
                                                    className="h-7 px-2 text-xs text-emerald-600 dark:text-emerald-400"
                                                    onClick={() => {
                                                        const url = apiClient.defaults.baseURL + '/wellness/reports/' + ev.pdf_report_path;
                                                        window.open(url, '_blank');
                                                    }}
                                                    title="Ver PDF"
                                                >
                                                    <FileText className="h-3.5 w-3.5" />
                                                </Button>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
