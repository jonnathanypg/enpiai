'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useTranslation } from 'react-i18next';
import { useQuery } from '@tanstack/react-query';
import { 
    CheckCircle2, 
    Circle, 
    ChevronUp, 
    ChevronDown, 
    Sparkles, 
    User,
    Bot, 
    Radio, 
    FileText, 
    HeartPulse, 
    PlayCircle,
    PartyPopper,
    CreditCard
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useOnboardingStore } from '@/store/use-onboarding-store';
import apiClient from '@/lib/api-client';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface DistributorSettings {
    name: string | null;
    email: string | null;
    phone: string | null;
    herbalife_id: string | null;
    personality_prompt: string | null;
    custom_instructions: string | null;
    personal_story: string | null;
    agent_name: string | null;
}

interface AgentConfigData {
    id: number;
}

interface Channel {
    channel_type: string;
    status: string;
}

interface Document {
    id: number;
}

interface WellnessEvaluation {
    id: number;
}

interface RoadmapData {
    coach_mode_enabled: boolean;
}

interface MembershipInfo {
    is_active: boolean;
    status: string;
}

export function OnboardingChecklistWidget() {
    const { t } = useTranslation();
    const router = useRouter();
    const { 
        completedSteps, 
        setCompletedSteps, 
        checklistExpanded, 
        setChecklistExpanded, 
        startTour 
    } = useOnboardingStore();
    
    // 1. Fetch settings
    const { data: settings } = useQuery({
        queryKey: ['distributor-settings'],
        queryFn: async () => {
            const { data } = await apiClient.get<{ data: DistributorSettings }>('/distributors/settings');
            return data.data;
        },
        refetchInterval: 5000,
    });

    // 2. Fetch agents
    const { data: agents } = useQuery({
        queryKey: ['agent-configs'],
        queryFn: async () => {
            const { data } = await apiClient.get<{ data: AgentConfigData[] }>('/agents');
            return data.data;
        },
        refetchInterval: 5000,
    });

    // 3. Fetch channels
    const { data: channels } = useQuery({
        queryKey: ['channels'],
        queryFn: async () => {
            const { data } = await apiClient.get<{ data: Channel[] }>('/channels');
            return data.data;
        },
        refetchInterval: 5000,
    });

    // 4. Fetch documents
    const { data: documents } = useQuery({
        queryKey: ['documents'],
        queryFn: async () => {
            const { data } = await apiClient.get<{ data: Document[] }>('/rag');
            return data.data;
        },
        refetchInterval: 5000,
    });

    // 5. Fetch evaluations
    const { data: evaluations } = useQuery({
        queryKey: ['evaluations'],
        queryFn: async () => {
            const { data } = await apiClient.get<{ data: WellnessEvaluation[] }>('/wellness/evaluations');
            return data.data;
        },
        refetchInterval: 5000,
    });

    // 6. Fetch coach roadmap
    const { data: roadmap } = useQuery({
        queryKey: ['coach-roadmap'],
        queryFn: async () => {
            const { data } = await apiClient.get<{ data: RoadmapData }>('/coach/roadmap');
            return data.data;
        },
        refetchInterval: 5000,
    });

    // 7. Fetch my subscription
    const { data: membership } = useQuery<MembershipInfo>({
        queryKey: ['my-subscription'],
        queryFn: async () => {
            const { data } = await apiClient.get('/billing/my-subscription');
            return data;
        },
        refetchInterval: 5000,
    });

    useEffect(() => {
        const liveCompleted: string[] = [];

        // 1. Profile settings validation
        if (
            settings && 
            settings.name && 
            settings.email && 
            settings.phone && 
            settings.herbalife_id
        ) {
            liveCompleted.push('profile');
        }

        // 2. Agent configuration validation (completed only if user has customized it)
        const hasCustomPersona = settings && (
            settings.personality_prompt || 
            settings.custom_instructions || 
            settings.personal_story ||
            (settings.agent_name && settings.agent_name !== 'Asistente' && settings.agent_name !== 'Assistant')
        );
        if (agents && agents.length > 0 && hasCustomPersona) {
            liveCompleted.push('agents');
        }

        // 3. WhatsApp channel connection validation
        if (channels && channels.some(c => c.channel_type === 'whatsapp' && c.status === 'active')) {
            liveCompleted.push('channels');
        }

        // 4. RAG documents uploaded validation
        if (documents && documents.length > 0) {
            liveCompleted.push('documents');
        }

        // 5. Wellness evaluations validation
        if (evaluations && evaluations.length > 0) {
            liveCompleted.push('wellness');
        }

        // 6. Coach mode validation
        if (roadmap && roadmap.coach_mode_enabled === true) {
            liveCompleted.push('coach');
        }

        // 7. Billing subscription validation (completed only if subscribed or courtesy, not trial)
        if (
            membership && 
            membership.is_active && 
            ['active', 'courtesy'].includes(membership.status)
        ) {
            liveCompleted.push('subscribe');
        }

        setCompletedSteps(liveCompleted);
    }, [settings, agents, channels, documents, evaluations, roadmap, membership]);

    const checklistItems = [
        {
            key: 'profile',
            title: t('onboarding.stepProfile'),
            desc: t('onboarding.stepProfileDesc'),
            href: '/settings',
            icon: User,
        },
        {
            key: 'agents',
            title: t('onboarding.stepAgents'),
            desc: t('onboarding.stepAgentsDesc'),
            href: '/agents',
            icon: Bot,
        },
        {
            key: 'channels',
            title: t('onboarding.stepChannels'),
            desc: t('onboarding.stepChannelsDesc'),
            href: '/channels',
            icon: Radio,
        },
        {
            key: 'documents',
            title: t('onboarding.stepDocuments'),
            desc: t('onboarding.stepDocumentsDesc'),
            href: '/documents',
            icon: FileText,
        },
        {
            key: 'wellness',
            title: t('onboarding.stepWellness'),
            desc: t('onboarding.stepWellnessDesc'),
            href: '/wellness',
            icon: HeartPulse,
        },
        {
            key: 'coach',
            title: t('onboarding.stepCoach'),
            desc: t('onboarding.stepCoachDesc'),
            href: '/coach',
            icon: Sparkles,
        },
        {
            key: 'subscribe',
            title: t('onboarding.stepSubscribe'),
            desc: t('onboarding.stepSubscribeDesc'),
            href: '/subscribe',
            icon: CreditCard,
        },
    ];

    const completedCount = checklistItems.filter(item => completedSteps.includes(item.key)).length;
    const progressPercent = Math.round((completedCount / checklistItems.length) * 100);
    const allCompleted = completedCount === checklistItems.length;

    const handleItemClick = (href: string) => {
        router.push(href);
    };

    // CRITICAL REQUIREMENT: Do not keep this widget floating if all steps are completed (activation complete).
    // This keeps the dashboard clutter-free.
    if (allCompleted) {
        return null;
    }

    return (
        <div className="fixed bottom-6 right-6 z-[9000] flex flex-col items-end gap-3 pointer-events-none">
            {/* Expanded panel */}
            {checklistExpanded && (
                <Card className="w-80 sm:w-96 shadow-2xl border !bg-white dark:!bg-zinc-950 !opacity-100 overflow-hidden rounded-2xl animate-fade-in pointer-events-auto">
                    {/* Header */}
                    <div className="p-4 bg-gradient-to-r from-emerald-600 via-teal-600 to-green-500 text-white flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Sparkles className="h-5 w-5 text-emerald-200 animate-pulse" />
                            <div>
                                <h4 className="font-bold text-sm tracking-tight">{t('onboarding.checklistTitle')}</h4>
                                <p className="text-[10px] text-emerald-100">{completedCount} de {checklistItems.length} completados</p>
                            </div>
                        </div>
                        <Button 
                            variant="ghost" 
                            size="icon" 
                            onClick={() => setChecklistExpanded(false)}
                            className="text-white hover:bg-white/10 rounded-full h-8 w-8"
                        >
                            <ChevronDown className="h-4 w-4" />
                        </Button>
                    </div>

                    {/* Progress Bar */}
                    <div className="h-1.5 w-full bg-muted/40 relative">
                        <div 
                            className="h-full bg-gradient-to-r from-emerald-500 via-teal-500 to-green-500 transition-all duration-500 ease-out"
                            style={{ width: `${progressPercent}%` }}
                        />
                    </div>

                    {/* Step list */}
                    <div className="p-4 max-h-[350px] overflow-y-auto space-y-3">
                        <div className="space-y-2.5">
                            {checklistItems.map((item, idx) => {
                                const isDone = completedSteps.includes(item.key);
                                const StepIcon = item.icon;
                                
                                return (
                                    <button
                                        key={item.key}
                                        onClick={() => handleItemClick(item.href)}
                                        className={cn(
                                            "w-full flex items-start gap-3 p-2.5 rounded-xl text-left border transition-all duration-300",
                                            isDone 
                                                ? "bg-green-500/5 border-green-500/20 hover:bg-green-500/10" 
                                                : "bg-muted/10 border-border/80 hover:bg-muted/50 hover:border-emerald-500/30"
                                        )}
                                    >
                                        <div className="mt-0.5 shrink-0">
                                            {isDone ? (
                                                <CheckCircle2 className="h-5 w-5 text-green-500 fill-green-500/10" />
                                            ) : (
                                                <Circle className="h-5 w-5 text-muted-foreground/60" />
                                            )}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-1.5">
                                                <StepIcon className={cn(
                                                    "h-3.5 w-3.5 shrink-0",
                                                    isDone ? "text-green-500" : "text-emerald-500"
                                                )} />
                                                <h5 className={cn(
                                                    "font-semibold text-xs leading-none text-foreground truncate",
                                                    isDone && "line-through text-muted-foreground"
                                                )}>
                                                    {item.title}
                                                </h5>
                                            </div>
                                            <p className="text-[10px] text-muted-foreground leading-normal mt-1 truncate">
                                                {item.desc}
                                            </p>
                                        </div>
                                    </button>
                                );
                            })}
                        </div>
                    </div>

                    {/* Footer */}
                    <div className="p-3 border-t bg-muted/20 flex justify-between items-center text-xs">
                        <button 
                            onClick={() => startTour(0)}
                            className="flex items-center gap-1 text-emerald-600 hover:text-emerald-700 font-semibold transition-colors"
                        >
                            <PlayCircle className="h-4 w-4" />
                            Reiniciar Tour
                        </button>
                        <span className="text-[10px] text-muted-foreground">EnpiAI Onboarding v1.0</span>
                    </div>
                </Card>
            )}

            {/* Floating toggle badge */}
            <button
                onClick={() => setChecklistExpanded(!checklistExpanded)}
                className="relative flex items-center justify-center h-12 w-12 rounded-full shadow-2xl transition-all duration-300 pointer-events-auto border hover:scale-105 active:scale-95 text-white bg-gradient-to-r from-emerald-600 via-teal-600 to-green-500 border-emerald-400"
                title={`${progressPercent}% Activado`}
            >
                <Sparkles className="h-5 w-5 animate-pulse" />
                <span className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500 border border-white text-[9px] font-extrabold text-white shadow-md">
                    {progressPercent}%
                </span>
            </button>
        </div>
    );
}
