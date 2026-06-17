'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
    Sparkles, 
    Award, 
    BookOpen, 
    Music, 
    CheckCircle2, 
    Play, 
    RefreshCw, 
    Trophy, 
    Target, 
    Flame,
    Volume2,
    CheckSquare,
    Square,
    Compass
} from 'lucide-react';
import { toast } from 'sonner';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import apiClient from '@/lib/api-client';
import { useTranslation } from 'react-i18next';

const getLevelTranslationKey = (lvl: string) => {
    switch (lvl) {
        case 'Distribuidor Independiente': return 'levels.distribuidor';
        case 'Consultor Mayor': return 'levels.consultor';
        case 'Constructor del Éxito': return 'levels.constructor';
        case 'Productor Calificado': return 'levels.productor';
        case 'Supervisor': return 'levels.supervisor';
        case 'Equipo del Mundo': return 'levels.mundo';
        case 'Equipo del Mundo Activo': return 'levels.mundo_activo';
        case 'GET': return 'levels.get';
        case 'Equipo de Millonarios': return 'levels.millonarios';
        case 'Equipo del Presidente': return 'levels.presidente';
        case 'Club del Chairman': return 'levels.chairman';
        case 'Círculo del Fundador': return 'levels.fundador';
        default: return '';
    }
};

interface RoadmapData {
    level: string;
    progress: number;
    coach_mode_enabled: boolean;
    coach_music_preference: string;
    daily_challenges: {
        id: string;
        label: string;
        is_completed: boolean;
    }[];
    weekly_goals: {
        id: string;
        label: string;
        is_completed: boolean;
    }[];
    monthly_goals: {
        id: string;
        label: string;
        is_completed: boolean;
    }[];
    resources: {
        music_playlist: string;
        music_playlist_label: string;
        eduardo_salazar_channel: string;
        metafisica_channel: string;
        recommended_books: string[];
    };
    last_research_advice?: string;
}

export default function CoachModePage() {
    const { t } = useTranslation();
    const queryClient = useQueryClient();
    const [coachAdvice, setCoachAdvice] = useState<string>('');
    const [researchAdvice, setResearchAdvice] = useState<string>('');

    // Fetch roadmap data
    const { data: roadmap, isLoading } = useQuery({
        queryKey: ['coach-roadmap'],
        queryFn: async () => {
            const { data } = await apiClient.get<{ data: RoadmapData }>('/coach/roadmap');
            return data.data;
        }
    });

    // Update settings (toggle coach mode, change level, change music)
    const updateSettingsMutation = useMutation({
        mutationFn: async (payload: Partial<{ coach_mode_enabled: boolean; coach_music_preference: string; herbalife_level: string }>) => {
            const { data } = await apiClient.post('/coach/settings', payload);
            return data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['coach-roadmap'] });
            toast.success(t('coachMode.configUpdated'));
        },
        onError: (err) => {
            toast.error(t('coachMode.configUpdateError'));
        }
    });

    // Toggle daily task status
    const toggleTaskMutation = useMutation({
        mutationFn: async (taskId: string) => {
            const { data } = await apiClient.post('/coach/tasks/toggle', { task_id: taskId });
            return data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['coach-roadmap'] });
            toast.success(t('coachMode.challengeUpdated'));
        },
        onError: (err) => {
            toast.error(t('coachMode.challengeUpdateError'));
        }
    });

    // Request immediate AI advice
    const requestAdviceMutation = useMutation({
        mutationFn: async () => {
            const { data } = await apiClient.post<{ data: { advice: string } }>('/coach/advice');
            return data.data;
        },
        onSuccess: (data) => {
            setCoachAdvice(data.advice);
            toast.success(t('coachMode.adviceGenerated'));
        },
        onError: (err) => {
            toast.error(t('coachMode.adviceError'));
        }
    });

    // Run Roadmap Researcher agent
    const runResearchMutation = useMutation({
        mutationFn: async () => {
            const { data } = await apiClient.post<{ data: { success: boolean; analysis: string } }>('/coach/research');
            return data.data;
        },
        onSuccess: (data) => {
            if (data.success) {
                setResearchAdvice(data.analysis);
                toast.success(t('coachMode.researchSuccess'));
            } else {
                toast.error(t('coachMode.researchAgentFailure'));
            }
        },
        onError: (err) => {
            toast.error(t('coachMode.researchInitError'));
        }
    });

    if (isLoading) {
        return (
            <div className="space-y-6">
                <Skeleton className="h-12 w-64" />
                <Skeleton className="h-64 w-full" />
                <Skeleton className="h-64 w-full" />
            </div>
        );
    }

    if (!roadmap) {
        return <div className="p-4 text-center">{t('coachMode.loadError')}</div>;
    }

    const {
        level,
        progress,
        coach_mode_enabled,
        coach_music_preference,
        daily_challenges,
        weekly_goals,
        monthly_goals,
        resources,
    } = roadmap;

    return (
        <div className="space-y-8 max-w-7xl mx-auto">
            {/* Header Banner */}
            <div className="relative rounded-3xl overflow-hidden bg-gradient-to-r from-emerald-700 via-teal-800 to-indigo-950 p-8 md:p-12 shadow-2xl border border-white/10 glass">
                <div className="relative z-10 max-w-3xl space-y-4">
                    <Badge variant="secondary" className="bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/30 border border-emerald-500/30 px-3 py-1">
                        <Flame className="w-3.5 h-3.5 mr-1 text-orange-400 animate-pulse" />
                        {t('coachMode.planMarketing')}
                    </Badge>
                    <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-white">
                        {t('sidebar.coach')}: <span className="bg-gradient-to-r from-emerald-400 to-cyan-300 bg-clip-text text-transparent">{t('coachMode.roadToPresident')}</span>
                    </h1>
                    <p className="text-gray-300 text-lg md:text-xl">
                        {t('coachMode.description')}
                    </p>
                </div>
                {/* Decorative glows */}
                <div className="absolute right-0 top-0 -translate-y-1/4 translate-x-1/4 w-96 h-96 rounded-full bg-emerald-500/20 blur-3xl" />
                <div className="absolute left-1/3 bottom-0 translate-y-1/2 w-96 h-96 rounded-full bg-indigo-500/20 blur-3xl" />
            </div>

            <div className="grid gap-8 lg:grid-cols-3">
                {/* Left Column: Stats & Setup */}
                <div className="lg:col-span-2 space-y-8">
                    {/* Progress Card */}
                    <Card className="border-emerald-500/10 bg-emerald-950/5 backdrop-blur-xl shadow-lg border relative overflow-hidden">
                        <CardHeader className="pb-4">
                            <CardTitle className="flex items-center gap-2 text-xl font-bold">
                                <Trophy className="w-5 h-5 text-yellow-400" />
                                {t('coachMode.successLadder', { progress })}
                            </CardTitle>
                            <CardDescription>{t('coachMode.currentPositionDesc')}</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            <div className="space-y-2">
                                <div className="flex justify-between text-sm font-semibold">
                                    <span className="text-emerald-400">{t(getLevelTranslationKey(level) || level)}</span>
                                    <span className="text-muted-foreground">{t('coachMode.presidentTeam')}</span>
                                </div>
                                <Progress value={progress} className="h-3 bg-emerald-950" />
                            </div>

                            <div className="grid gap-4 md:grid-cols-2">
                                <div className="space-y-2">
                                    <label className="text-sm font-medium text-muted-foreground">{t('coachMode.currentLevel')}</label>
                                    <select
                                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                                        value={level}
                                        onChange={(e) => updateSettingsMutation.mutate({ herbalife_level: e.target.value })}
                                    >
                                        <option value="Distribuidor Independiente">{t('levels.distribuidor')}</option>
                                        <option value="Consultor Mayor">{t('levels.consultor')}</option>
                                        <option value="Constructor del Éxito">{t('levels.constructor')}</option>
                                        <option value="Productor Calificado">{t('levels.productor')}</option>
                                        <option value="Supervisor">{t('levels.supervisor')}</option>
                                        <option value="Equipo del Mundo">{t('levels.mundo')}</option>
                                        <option value="Equipo del Mundo Activo">{t('levels.mundo_activo')}</option>
                                        <option value="GET">{t('levels.get')}</option>
                                        <option value="Equipo de Millonarios">{t('levels.millonarios')}</option>
                                        <option value="Equipo del Presidente">{t('levels.presidente')}</option>
                                        <option value="Club del Chairman">{t('levels.chairman')}</option>
                                        <option value="Círculo del Fundador">{t('levels.fundador')}</option>
                                    </select>
                                </div>

                                <div className="flex items-center justify-between border rounded-lg p-4 bg-background/50">
                                    <div className="space-y-0.5">
                                        <div className="text-sm font-semibold">{t('coachMode.activeCoachService')}</div>
                                        <div className="text-xs text-muted-foreground">{t('coachMode.enableChallenges')}</div>
                                    </div>
                                    <Switch
                                        checked={coach_mode_enabled}
                                        onCheckedChange={(checked) => updateSettingsMutation.mutate({ coach_mode_enabled: checked })}
                                    />
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Challenges List Card */}
                    <Card className="border-indigo-500/10 shadow-lg">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-xl font-bold">
                                <Target className="w-5 h-5 text-indigo-400" />
                                {t('coachMode.challengesTitle')}
                            </CardTitle>
                            <CardDescription>{t('coachMode.challengesDesc')}</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <Tabs defaultValue="daily" className="w-full">
                                <TabsList className="grid w-full grid-cols-3 mb-6 bg-muted p-1 rounded-xl">
                                    <TabsTrigger value="daily" className="rounded-lg py-2">{t('coachMode.daily')}</TabsTrigger>
                                    <TabsTrigger value="weekly" className="rounded-lg py-2">{t('coachMode.weekly')}</TabsTrigger>
                                    <TabsTrigger value="monthly" className="rounded-lg py-2">{t('coachMode.monthly')}</TabsTrigger>
                                </TabsList>

                                <TabsContent value="daily" className="space-y-4">
                                    {daily_challenges.length === 0 ? (
                                        <p className="text-center text-muted-foreground py-4">{t('coachMode.noDailyChallenges')}</p>
                                    ) : (
                                        <div className="grid gap-3">
                                            {daily_challenges.map((c) => (
                                                <div 
                                                    key={c.id} 
                                                    onClick={() => toggleTaskMutation.mutate(c.id)}
                                                    className={`flex items-center gap-3 p-4 rounded-xl border cursor-pointer transition-all duration-200 ${
                                                        c.is_completed 
                                                        ? 'bg-emerald-50 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-500/30 text-emerald-800 dark:text-emerald-200' 
                                                        : 'bg-card hover:bg-slate-100 dark:hover:bg-slate-900 border-border text-foreground'
                                                    }`}
                                                >
                                                    {c.is_completed ? (
                                                        <CheckSquare className="w-5 h-5 text-emerald-400" />
                                                    ) : (
                                                        <Square className="w-5 h-5 text-muted-foreground" />
                                                    )}
                                                    <span className="text-sm font-semibold">{c.label}</span>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </TabsContent>

                                <TabsContent value="weekly" className="space-y-4">
                                    <div className="grid gap-3">
                                        {weekly_goals.map((g) => (
                                            <div 
                                                key={g.id} 
                                                className="flex items-center gap-3 p-4 rounded-xl border border-border bg-card/50"
                                            >
                                                <Square className="w-5 h-5 text-muted-foreground" />
                                                <span className="text-sm font-semibold text-foreground">{g.label}</span>
                                                <Badge variant="outline" className="ml-auto text-indigo-500 dark:text-indigo-400 border-indigo-500/30 dark:border-indigo-500/20">{t('coachMode.weeklyBadge')}</Badge>
                                            </div>
                                        ))}
                                    </div>
                                </TabsContent>

                                <TabsContent value="monthly" className="space-y-4">
                                    <div className="grid gap-3">
                                        {monthly_goals.map((g) => (
                                            <div 
                                                key={g.id} 
                                                className="flex items-center gap-3 p-4 rounded-xl border border-border bg-card/50"
                                            >
                                                <Square className="w-5 h-5 text-muted-foreground" />
                                                <span className="text-sm font-semibold text-foreground">{g.label}</span>
                                                <Badge variant="outline" className="ml-auto text-amber-600 dark:text-amber-400 border-amber-500/30 dark:border-amber-500/20">{t('coachMode.monthlyBadge')}</Badge>
                                            </div>
                                        ))}
                                    </div>
                                </TabsContent>
                            </Tabs>
                        </CardContent>
                    </Card>
                </div>

                {/* Right Column: AI Coach Advice & Resources */}
                <div className="space-y-8">
                    {/* Music Preferences */}
                    <Card className="border-indigo-500/10 shadow-lg">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-xl font-bold">
                                <Music className="w-5 h-5 text-cyan-400" />
                                {t('coachMode.wealthFrequencies')}
                            </CardTitle>
                            <CardDescription>{t('coachMode.musicDesc')}</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <select
                                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                                value={coach_music_preference}
                                onChange={(e) => updateSettingsMutation.mutate({ coach_music_preference: e.target.value })}
                            >
                                <option value="spanish">{t('coachMode.musicEs')}</option>
                                <option value="english">{t('coachMode.musicEn')}</option>
                                <option value="none">{t('coachMode.musicNone')}</option>
                            </select>
                            <Button 
                                variant="outline" 
                                className="w-full flex items-center justify-center gap-2 border-cyan-500/20 hover:bg-cyan-500/10 hover:text-cyan-300"
                                onClick={() => window.open(resources.music_playlist, '_blank')}
                            >
                                <Play className="w-4 h-4 fill-cyan-400 text-cyan-400" />
                                {t('coachMode.listenPlaylist')}
                            </Button>
                        </CardContent>
                    </Card>

                    {/* AI Coach Assistant Interaction Card */}
                    <Card className="border-indigo-500/10 bg-indigo-950/5 backdrop-blur-xl shadow-lg border relative overflow-hidden">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-xl font-bold">
                                <Sparkles className="w-5 h-5 text-emerald-400" />
                                {t('coachMode.aiCoachMessage')}
                            </CardTitle>
                            <CardDescription>{t('coachMode.aiCoachDesc')}</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="space-y-2">
                                <Button 
                                    className="w-full bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-700 hover:to-teal-600 text-white font-bold"
                                    onClick={() => requestAdviceMutation.mutate()}
                                    disabled={requestAdviceMutation.isPending}
                                >
                                    {requestAdviceMutation.isPending ? (
                                        <>
                                            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                                            {t('coachMode.generatingAdvice')}
                                        </>
                                    ) : t('coachMode.getAdvice')}
                                </Button>

                                <Button 
                                    variant="secondary"
                                    className="w-full font-bold"
                                    onClick={() => runResearchMutation.mutate()}
                                    disabled={runResearchMutation.isPending}
                                >
                                    {runResearchMutation.isPending ? (
                                        <>
                                            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                                            {t('coachMode.analyzingProgress')}
                                        </>
                                    ) : (
                                        <>
                                            <Compass className="w-4 h-4 mr-2 text-cyan-400" />
                                            {t('coachMode.researchMilestones')}
                                        </>
                                    )}
                                </Button>
                            </div>

                            {coachAdvice && (
                                <div className="p-4 rounded-xl border border-emerald-500/20 bg-emerald-950/15 text-sm text-emerald-300/90 whitespace-pre-wrap">
                                    {coachAdvice}
                                </div>
                            )}

                            {researchAdvice && (
                                <div className="p-4 rounded-xl border border-cyan-500/20 bg-cyan-950/15 text-sm text-cyan-300/90 whitespace-pre-wrap">
                                    <div className="font-bold mb-2 text-cyan-300 flex items-center gap-1.5">
                                        <Award className="w-4 h-4 text-cyan-400" />
                                        {t('coachMode.recommendedMilestones')}
                                    </div>
                                    {researchAdvice}
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    {/* Resources Links Card */}
                    <Card className="border-indigo-500/10 shadow-lg">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-xl font-bold">
                                <BookOpen className="w-5 h-5 text-indigo-400" />
                                {t('coachMode.growthResources')}
                            </CardTitle>
                            <CardDescription>{t('coachMode.resourcesDesc')}</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="grid gap-2">
                                <Button 
                                    variant="outline" 
                                    className="w-full flex items-center justify-start gap-3 border-border hover:bg-muted text-foreground"
                                    onClick={() => window.open(resources.eduardo_salazar_channel, '_blank')}
                                >
                                    <Volume2 className="w-4 h-4 text-red-500" />
                                    <span>{t('coachMode.eduardoSalazar')}</span>
                                </Button>
                                <Button 
                                    variant="outline" 
                                    className="w-full flex items-center justify-start gap-3 border-border hover:bg-muted text-foreground"
                                    onClick={() => window.open(resources.metafisica_channel, '_blank')}
                                >
                                    <Volume2 className="w-4 h-4 text-purple-400" />
                                    <span>{t('coachMode.metafisica')}</span>
                                </Button>
                            </div>

                            {resources.recommended_books.length > 0 && (
                                <div className="space-y-2 pt-2 border-t border-white/10">
                                    <h4 className="text-xs font-semibold uppercase text-muted-foreground tracking-wider">{t('coachMode.recommendedReading')}</h4>
                                    <ul className="text-xs space-y-1.5 text-muted-foreground">
                                        {resources.recommended_books.map((b, i) => (
                                            <li key={i} className="flex items-start gap-2">
                                                <span className="text-emerald-400">•</span>
                                                <span>{b}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    {/* President's Tips Section - Hidden temporarily */}
                    {false && (
                        <Card className="border-amber-500/10 bg-amber-950/5 backdrop-blur-xl border shadow-lg">
                            <CardHeader>
                                <CardTitle className="text-xl font-bold flex items-center gap-2">
                                    <Award className="w-5 h-5 text-amber-400" />
                                    Consejos de Presidentes
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="text-sm space-y-4">
                                <div className="p-4 rounded-xl border border-amber-500/20 bg-amber-950/15 text-amber-200/90 italic">
                                    &ldquo;El secreto en Herbalife no es solo reclutar, sino enseñar a tu gente a duplicarse. Si tú sabes hacer una evaluación de bienestar, enseña a tus distribuidores en sus primeras 48 horas.&rdquo;
                                    <div className="mt-2 text-xs font-bold text-amber-400 text-right">— María (Círculo de Fundadores)</div>
                                </div>
                            </CardContent>
                        </Card>
                    )}
                </div>
            </div>
        </div>
    );
}
