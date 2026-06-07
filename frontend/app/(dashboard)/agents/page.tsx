'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Bot, Save, Loader2, Sparkles, MessageSquare, Settings2, Zap, Volume2 } from 'lucide-react';
import { toast } from 'sonner';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import apiClient from '@/lib/api-client';
import { useTranslation } from 'react-i18next';

interface AgentPersona {
    agent_name: string | null;
    agent_gender: string | null;
    personality_prompt: string | null;
    custom_instructions: string | null;
    personal_story: string | null;
    preferred_voice?: string | null;
}

interface AgentConfigData {
    id: number;
    name: string;
    description: string | null;
    agent_type: string;
    tone: string;
    objective: string;
    system_prompt: string | null;
    priority: number;
    is_active: boolean;
    features: AgentFeature[];
}

interface AgentFeature {
    id: number;
    category: string;
    name: string;
    label: string;
    description: string;
    is_enabled: boolean;
    order: number;
}

const TONE_OPTIONS = [
    { value: 'friendly', labelKey: 'common.friendly', emoji: '😊' },
    { value: 'professional', labelKey: 'common.professional', emoji: '💼' },
    { value: 'sales', labelKey: 'common.sales', emoji: '🎯' },
    { value: 'wellness_coach', labelKey: 'common.wellness_coach', emoji: '🌿' },
    { value: 'support', labelKey: 'common.support', emoji: '🛟' },
    { value: 'casual', labelKey: 'common.casual', emoji: '😎' },
    { value: 'formal', labelKey: 'common.formal', emoji: '🎩' },
];

const OBJECTIVE_OPTIONS = [
    { value: 'general', labelKey: 'common.general' },
    { value: 'customer_service', labelKey: 'common.customer_service' },
    { value: 'sales', labelKey: 'common.sales' },
    { value: 'scheduling', labelKey: 'common.scheduling' },
    { value: 'lead_qualification', labelKey: 'common.lead_qualification' },
    { value: 'wellness_evaluation', labelKey: 'common.wellness_evaluation' },
    { value: 'distributor_assistant', labelKey: 'common.distributor_assistant' },
];

const CATEGORY_LABELS: Record<string, { labelKey: string; icon: string }> = {
    channel: { labelKey: 'agentSetup.integrations', icon: '📡' },
    integration: { labelKey: 'agentSetup.integrations', icon: '🔗' },
    skill: { labelKey: 'agentSetup.tools', icon: '🧠' },
    ai_feature: { labelKey: 'agentSetup.aiFeatures', icon: '✨' },
};

export default function AgentSetupPage() {
    const { t } = useTranslation();
    const queryClient = useQueryClient();

    // --- Persona data (distributor-level) ---
    const { data: settings, isLoading: loadingSettings } = useQuery({
        queryKey: ['distributor-settings'],
        queryFn: async () => {
            const { data } = await apiClient.get<{ data: AgentPersona }>('/distributors/settings');
            return data.data;
        },
    });

    // --- Agent config data ---
    const { data: agents, isLoading: loadingAgents } = useQuery({
        queryKey: ['agent-configs'],
        queryFn: async () => {
            const { data } = await apiClient.get<{ data: AgentConfigData[] }>('/agents');
            return data.data;
        },
    });

    const agent = agents?.[0]; // Primary agent (highest priority)

    // --- Form State ---
    const [agentName, setAgentName] = useState('');
    const [agentGender, setAgentGender] = useState('neutral');
    const [persona, setPersona] = useState('');
    const [customInstructions, setCustomInstructions] = useState('');
    const [personalStory, setPersonalStory] = useState('');
    const [tone, setTone] = useState('friendly');
    const [objective, setObjective] = useState('general');
    const [features, setFeatures] = useState<Record<string, boolean>>({});

    const [preferredVoice, setPreferredVoice] = useState('es-EC-LuisNeural');
    const [testText, setTestText] = useState('¡Hola! Estoy probando mi nueva voz de inteligencia artificial en Enpi AI.');
    const [testingVoice, setTestingVoice] = useState(false);

    // --- Dynamic Voices list query ---
    const { data: voicesResponse } = useQuery({
        queryKey: ['voice-voices'],
        queryFn: async () => {
            const { data } = await apiClient.get<any[]>('/voice/voices');
            return data;
        }
    });
    const voicesList = voicesResponse || [];

    // Populate form when data loads
    useEffect(() => {
        if (settings) {
            setAgentName(settings.agent_name || '');
            setAgentGender(settings.agent_gender || 'neutral');
            setPersona(settings.personality_prompt || '');
            setCustomInstructions(settings.custom_instructions || '');
            setPersonalStory(settings.personal_story || '');
            setPreferredVoice(settings.preferred_voice || 'es-EC-LuisNeural');
        }
    }, [settings]);

    useEffect(() => {
        if (agent) {
            setTone(agent.tone || 'friendly');
            setObjective(agent.objective || 'general');
            const featureMap: Record<string, boolean> = {};
            agent.features.forEach((f) => {
                featureMap[f.name] = f.is_enabled;
            });
            setFeatures(featureMap);
        }
    }, [agent]);

    // Voice testing action
    const handleTestVoice = async () => {
        if (testingVoice || !testText.trim()) return;
        setTestingVoice(true);
        try {
            const response = await apiClient.post('/voice/synthesize', {
                text: testText,
                voice_name: preferredVoice
            }, {
                responseType: 'blob'
            });
            const blob = new Blob([response.data], { type: 'audio/mpeg' });
            const url = URL.createObjectURL(blob);
            const audio = new Audio(url);
            audio.play();
        } catch (error) {
            console.error('Failed to test voice:', error);
            toast.error('Error al generar la prueba de voz');
        } finally {
            setTestingVoice(false);
        }
    };

    // --- Mutations ---
    const savePersonaMutation = useMutation({
        mutationFn: async () => {
            await apiClient.put('/distributors/agent-persona', {
                agent_name: agentName,
                agent_gender: agentGender,
                personality_prompt: persona,
                custom_instructions: customInstructions,
                preferred_voice: preferredVoice,
            });
        },
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['distributor-settings'] }),
    });

    const saveStoryMutation = useMutation({
        mutationFn: async () => {
            await apiClient.put('/distributors/settings', {
                personal_story: personalStory,
            });
        },
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['distributor-settings'] }),
    });

    const saveAgentMutation = useMutation({
        mutationFn: async () => {
            if (!agent) return;
            await apiClient.put(`/agents/${agent.id}`, {
                tone, objective,
            });
        },
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['agent-configs'] }),
    });

    const saveFeaturesMutation = useMutation({
        mutationFn: async () => {
            if (!agent) return;
            await apiClient.put(`/agents/${agent.id}/features`, { features });
        },
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['agent-configs'] }),
    });

    const handleSaveAll = async () => {
        try {
            await Promise.all([
                savePersonaMutation.mutateAsync(),
                saveStoryMutation.mutateAsync(),
                ...(agent ? [saveAgentMutation.mutateAsync(), saveFeaturesMutation.mutateAsync()] : []),
            ]);
            toast.success(t('common.success', { defaultValue: '¡Configuración guardada!' }));
        } catch (error: unknown) {
            const message =
                (error as { response?: { data?: { error?: string } } })?.response?.data?.error ||
                t('common.error', { defaultValue: 'Error al guardar' });
            toast.error(message);
        }
    };

    const isSaving = savePersonaMutation.isPending || saveAgentMutation.isPending || saveFeaturesMutation.isPending || saveStoryMutation.isPending;

    if (loadingSettings || loadingAgents) {
        return (
            <div className="mx-auto max-w-3xl space-y-6">
                <Skeleton className="h-10 w-48" />
                <Skeleton className="h-64 w-full" />
                <Skeleton className="h-48 w-full" />
                <Skeleton className="h-64 w-full" />
            </div>
        );
    }

    // Group features by category
    const groupedFeatures = (agent?.features || []).reduce<Record<string, AgentFeature[]>>((acc, f) => {
        if (!acc[f.category]) acc[f.category] = [];
        acc[f.category].push(f);
        return acc;
    }, {});

    return (
        <div className="mx-auto max-w-3xl space-y-8 pb-12">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="flex items-center gap-2 text-3xl font-bold tracking-tight">
                        <Bot className="h-7 w-7 text-primary" />
                        {t('agentSetup.title')}
                    </h2>
                    <p className="text-muted-foreground">
                        {t('agentSetup.description')}
                    </p>
                </div>
                <Button onClick={handleSaveAll} disabled={isSaving} size="lg">
                    {isSaving ? (
                        <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            {t('common.saving', { defaultValue: 'Guardando...' })}
                        </>
                    ) : (
                        <>
                            <Save className="mr-2 h-4 w-4" />
                            {t('agentSetup.saveChanges')}
                        </>
                    )}
                </Button>
            </div>

            {/* Card 1: Identity & Persona */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Sparkles className="h-5 w-5 text-primary" />
                        {t('agentSetup.profileTitle')}
                    </CardTitle>
                    <CardDescription>
                        {t('agentSetup.profileDescription')}
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    <div className="grid gap-6 md:grid-cols-2">
                        <div className="space-y-2">
                            <Label htmlFor="agent_name">{t('agentSetup.agentName')}</Label>
                            <Input
                                id="agent_name"
                                placeholder="e.g. Luna, Max, Asistente"
                                value={agentName}
                                onChange={(e) => setAgentName(e.target.value)}
                            />
                            <p className="text-xs text-muted-foreground">
                                {t('agentSetup.agentNameHelp')}
                            </p>
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="agent_gender">{t('agentSetup.agentGender')}</Label>
                            <select
                                id="agent_gender"
                                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                                value={agentGender}
                                onChange={(e) => setAgentGender(e.target.value)}
                            >
                                <option value="neutral">{t('agentSetup.gender.neutral')}</option>
                                <option value="female">{t('agentSetup.gender.female')}</option>
                                <option value="male">{t('agentSetup.gender.male')}</option>
                            </select>
                        </div>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="persona">
                            {t('agentSetup.agentPersonality')}{' '}
                            <span className="text-muted-foreground">({t('common.optional', { defaultValue: 'opcional' })})</span>
                        </Label>
                        <Textarea
                            id="persona"
                            placeholder={t('agentSetup.agentPersonalityPlaceholder')}
                            value={persona}
                            onChange={(e) => setPersona(e.target.value)}
                            rows={4}
                        />
                        <p className="text-xs text-muted-foreground">
                            {t('agentSetup.agentPersonalityHelp')}
                        </p>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="custom_instructions">
                            {t('agentSetup.customInstructions')}{' '}
                            <span className="text-muted-foreground">({t('common.optional', { defaultValue: 'opcional' })})</span>
                        </Label>
                        <Textarea
                            id="custom_instructions"
                            placeholder={t('agentSetup.customInstructionsPlaceholder', { defaultValue: 'ej. Nunca recomiende batidos de chocolate. Siempre pregunte por alergias alimentarias antes de sugerir productos.' })}
                            value={customInstructions}
                            onChange={(e) => setCustomInstructions(e.target.value)}
                            rows={3}
                        />
                        <p className="text-xs text-muted-foreground">
                            {t('agentSetup.customInstructionsHelp')}
                        </p>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="personal_story">
                            {t('agentSetup.personalStory')}{' '}
                            <span className="text-muted-foreground">({t('common.optional', { defaultValue: 'opcional' })})</span>
                        </Label>
                        <Textarea
                            id="personal_story"
                            placeholder={t('agentSetup.personalStoryPlaceholder', { defaultValue: 'ej. Soy distribuidor Herbalife desde 2018. Mi pasión es ayudar a las personas a alcanzar su peso ideal a través de una alimentación balanceada...' })}
                            value={personalStory}
                            onChange={(e) => setPersonalStory(e.target.value)}
                            rows={3}
                        />
                        <p className="text-xs text-muted-foreground">
                            {t('agentSetup.personalStoryHelp')}
                        </p>
                    </div>
                </CardContent>
            </Card>

            {/* Card 2: Tone & Objective */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <MessageSquare className="h-5 w-5 text-primary" />
                        {t('agentSetup.behaviorTitle')}
                    </CardTitle>
                    <CardDescription>
                        {t('agentSetup.behaviorDescription')}
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    <div className="grid gap-6 md:grid-cols-2">
                        <div className="space-y-2">
                            <Label>{t('agentSetup.toneLabel')}</Label>
                            <div className="grid grid-cols-2 gap-2">
                                {TONE_OPTIONS.map((opt) => (
                                    <button
                                        key={opt.value}
                                        type="button"
                                        onClick={() => setTone(opt.value)}
                                        className={`flex items-center gap-2 rounded-lg border p-3 text-sm font-medium transition-all hover:border-primary/50 ${
                                            tone === opt.value
                                                ? 'border-primary bg-primary/5 text-primary shadow-sm'
                                                : 'border-border text-muted-foreground'
                                        }`}
                                    >
                                        <span>{opt.emoji}</span>
                                        <span>{t(opt.labelKey)}</span>
                                    </button>
                                ))}
                            </div>
                        </div>
                        <div className="space-y-2">
                            <Label>{t('agentSetup.objectiveLabel')}</Label>
                            <select
                                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                                value={objective}
                                onChange={(e) => setObjective(e.target.value)}
                            >
                                {OBJECTIVE_OPTIONS.map((opt) => (
                                    <option key={opt.value} value={opt.value}>
                                        {t(opt.labelKey)}
                                    </option>
                                ))}
                            </select>
                            <p className="text-xs text-muted-foreground">
                                {t('agentSetup.objectiveHelp')}
                            </p>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Card 3: Configuración de Voz (IAGS Protocol) */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Volume2 className="h-5 w-5 text-primary" />
                        Configuración de Voz (IAGS Protocol)
                    </CardTitle>
                    <CardDescription>
                        Selecciona el clon de voz neural que utilizará tu agente para responder notas de voz por WhatsApp y Chat Web.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    <div className="grid gap-6 md:grid-cols-2">
                        <div className="space-y-2">
                            <Label htmlFor="preferred_voice">Clon de Voz Neural</Label>
                            <select
                                id="preferred_voice"
                                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                                value={preferredVoice}
                                onChange={(e) => setPreferredVoice(e.target.value)}
                            >
                                {voicesList.length > 0 ? (
                                    voicesList.map((v: any) => (
                                        <option key={v.id} value={v.id}>
                                            {v.name} ({v.lang})
                                        </option>
                                    ))
                                ) : (
                                    <>
                                        <option value="es-EC-LuisNeural">Luis (Ecuador - Masculino) (es-EC)</option>
                                        <option value="es-EC-RamonaNeural">Ramona (Ecuador - Femenino) (es-EC)</option>
                                        <option value="es-MX-DaliaNeural">Dalia (México - Femenino) (es-MX)</option>
                                        <option value="es-MX-JorgeNeural">Jorge (México - Masculino) (es-MX)</option>
                                        <option value="es-US-PalomaNeural">Paloma (USA/Latam - Femenino) (es-US)</option>
                                        <option value="es-US-AlonsoNeural">Alonso (USA/Latam - Masculino) (es-US)</option>
                                        <option value="es-ES-ElviraNeural">Elvira (España - Femenino) (es-ES)</option>
                                        <option value="es-ES-AlvaroNeural">Alvaro (España - Masculino) (es-ES)</option>
                                    </>
                                )}
                            </select>
                            <p className="text-xs text-muted-foreground">
                                Las voces neurales de alta fidelidad proveen una conversación humanizada de acuerdo al acento regional de tus prospectos.
                            </p>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="test_voice_text">Probar Sintetizador de Voz</Label>
                            <div className="flex gap-2">
                                <Input
                                    id="test_voice_text"
                                    value={testText}
                                    onChange={(e) => setTestText(e.target.value)}
                                    placeholder="Escribe un mensaje de prueba..."
                                    className="flex-1"
                                />
                                <Button 
                                    type="button" 
                                    variant="secondary" 
                                    onClick={handleTestVoice}
                                    disabled={testingVoice || !testText.trim()}
                                >
                                    {testingVoice ? (
                                        <Loader2 className="h-4 w-4 animate-spin" />
                                    ) : (
                                        "Probar"
                                    )}
                                </Button>
                            </div>
                            <p className="text-xs text-muted-foreground">
                                Escucha una muestra del tono de voz seleccionado directamente en tu navegador.
                            </p>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Card 4: Feature Toggles */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Zap className="h-5 w-5 text-primary" />
                        {t('agentSetup.featuresTitle')}
                    </CardTitle>
                    <CardDescription>
                        {t('agentSetup.featuresDescription')}
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    {Object.entries(groupedFeatures)
                        .sort(([a], [b]) => {
                            const order = ['skill', 'ai_feature', 'channel', 'integration'];
                            return order.indexOf(a) - order.indexOf(b);
                        })
                        .map(([category, feats], idx) => (
                            <div key={category}>
                                {idx > 0 && <Separator className="mb-6" />}
                                <h4 className="mb-4 text-sm font-semibold uppercase tracking-wider text-muted-foreground">
                                    {CATEGORY_LABELS[category]?.icon} {t(CATEGORY_LABELS[category]?.labelKey || category)}
                                </h4>
                                <div className="grid gap-3 md:grid-cols-2">
                                    {feats
                                        .sort((a, b) => a.order - b.order)
                                        .map((feat) => (
                                            <div
                                                key={feat.name}
                                                className={`flex items-center justify-between rounded-lg border p-3 transition-colors ${
                                                    features[feat.name]
                                                        ? 'border-primary/30 bg-primary/5'
                                                        : 'border-border'
                                                }`}
                                            >
                                                <div className="space-y-0.5 pr-4">
                                                    <p className="text-sm font-medium leading-none">
                                                        {feat.label}
                                                    </p>
                                                    {feat.description && (
                                                        <p className="text-xs text-muted-foreground">
                                                            {feat.description}
                                                        </p>
                                                    )}
                                                </div>
                                                <Switch
                                                    checked={features[feat.name] || false}
                                                    onCheckedChange={(checked) =>
                                                        setFeatures((prev) => ({
                                                            ...prev,
                                                            [feat.name]: checked,
                                                        }))
                                                    }
                                                />
                                            </div>
                                        ))}
                                </div>
                            </div>
                        ))}

                    {Object.keys(groupedFeatures).length === 0 && (
                        <div className="flex flex-col items-center justify-center p-8 text-center text-muted-foreground">
                            <Settings2 className="mb-2 h-8 w-8 opacity-20" />
                            <p>{t('agentSetup.noAgentConfigured')}</p>
                            <p className="text-xs">{t('agentSetup.noAgentConfiguredHelp')}</p>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
