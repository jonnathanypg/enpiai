'use client';

import { useState, use, useMemo, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { 
    ArrowRight, 
    ArrowLeft, 
    Loader2, 
    Download, 
    Share2, 
    MessageCircle, 
    Send, 
    Languages, 
    Sparkles, 
    Activity, 
    Heart, 
    Check, 
    Moon, 
    Droplets, 
    Target, 
    User, 
    Scale, 
    Bot, 
    Zap, 
    ShieldCheck
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardFooter, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { 
    DropdownMenu, 
    DropdownMenuContent, 
    DropdownMenuItem, 
    DropdownMenuTrigger 
} from '@/components/ui/dropdown-menu';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { toast } from 'sonner';
import apiClient from '@/lib/api-client';
import { ThemeToggle } from '@/components/shared/theme-toggle';

// ── Symptom definitions (keyed to translation file) ──────────────────────
const SYMPTOM_GROUPS = [
    {
        category: 'symptomsDigestive',
        icon: '🥗',
        items: ['s1', 's2', 's3', 's4', 's5', 's6', 's7'],
    },
    {
        category: 'symptomsCardiovascular',
        icon: '❤️',
        items: ['s8', 's9', 's10', 's11', 's33'],
    },
    {
        category: 'symptomsMusculoskeletal',
        icon: '🦴',
        items: ['s12', 's13', 's14', 's15', 's16', 's17', 's18', 's19'],
    },
    {
        category: 'symptomsRespiratory',
        icon: '🫁',
        items: ['s20', 's21', 's22', 's23', 's24'],
    },
    {
        category: 'symptomsNeurological',
        icon: '🧠',
        items: ['s30', 's31', 's32'],
    },
    {
        category: 'symptomsGeneral',
        icon: '⚡',
        items: ['s25', 's26', 's27', 's28', 's29'],
    },
];

// ── Zod Schema ────────────────────────────────────────────────────────────
const evaluationSchema = z.object({
    // Step 1 – Personal
    age: z.string().min(1, 'Required'),
    gender: z.enum(['female', 'male', 'other']),
    // Step 2 – Measurements & Vitals
    height_cm: z.string().min(1, 'Required'),
    weight_kg: z.string().min(1, 'Required'),
    blood_pressure: z.string().optional(),
    pulse: z.string().optional(),
    energy_level: z.string().optional(),
    // Step 3 – Symptoms (managed outside zod via local state)
    // Step 4 – Lifestyle
    primary_goal: z.string().min(1, 'Required'),
    activity_level: z.enum(['sedentary', 'light', 'moderate', 'active', 'very_active']),
    meals_per_day: z.string().min(1, 'Required'),
    exercise_frequency: z.string().optional(),
    water_intake_liters: z.string().optional(),
    sleep_hours: z.string().optional(),
    sleep_quality: z.string().optional(),
    observations: z.string().optional(),
    // Step 5 – Contact
    first_name: z.string().min(2, 'Required'),
    email: z.string().email('Invalid email'),
    phone: z.string().min(8, 'Required'),
});

type EvaluationFormValues = z.infer<typeof evaluationSchema>;

const TOTAL_STEPS = 7; // intro(0) + personal(1) + body(2) + symptoms(3) + lifestyle(4) + contact(5) + results(6)

export default function EvaluationPage({ params }: { params: Promise<{ distributor_id: string }> }) {
    const resolvedParams = use(params);
    const distributor_id = resolvedParams.distributor_id;
    const { t, i18n } = useTranslation();
    const [step, setStep] = useState(0);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [selectedSymptoms, setSelectedSymptoms] = useState<string[]>([]);
    const [activeSymptomTab, setActiveSymptomTab] = useState('symptomsDigestive');
    const [resultData, setResultData] = useState<any>(null);
    const [isPolling, setIsPolling] = useState(false);

    // Fetch distributor public profile for language preference and coach details
    const { data: profile } = useQuery({
        queryKey: ['public-distributor', distributor_id],
        queryFn: async () => {
            const { data } = await apiClient.get(`/distributors/public/${distributor_id}`);
            return data.data;
        },
    });

    const [hasInitializedLanguage, setHasInitializedLanguage] = useState(false);

    useEffect(() => {
        if (profile?.language && !hasInitializedLanguage) {
            i18n.changeLanguage(profile.language);
            setHasInitializedLanguage(true);
        }
    }, [profile?.language, hasInitializedLanguage, i18n]);

    const {
        register,
        handleSubmit,
        trigger,
        setValue,
        watch,
        formState: { errors },
    } = useForm<EvaluationFormValues>({
        resolver: zodResolver(evaluationSchema),
        defaultValues: {
            gender: 'female',
            activity_level: 'moderate',
            meals_per_day: '3',
            water_intake_liters: '2.0',
            sleep_hours: '7',
            sleep_quality: 'good',
            energy_level: '7',
        },
        mode: 'onChange',
    });

    const currentGender = watch('gender');
    const currentActivity = watch('activity_level');
    const currentSleepQuality = watch('sleep_quality');
    const currentEnergy = watch('energy_level') || '7';
    const currentGoal = watch('primary_goal');
    const watchHeight = watch('height_cm');
    const watchWeight = watch('weight_kg');

    // ── Live BMI & Health Calculation ───────────────────────────────────────
    const liveCalculations = useMemo(() => {
        const h = parseFloat(watchHeight);
        const w = parseFloat(watchWeight);
        if (!h || !w || h <= 0 || w <= 0) return null;

        const hM = h / 100.0;
        const bmi = w / (hM * hM);
        
        let category = 'Normal';
        let color = 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20';
        if (bmi < 18.5) {
            category = 'Bajo Peso';
            color = 'text-amber-500 bg-amber-500/10 border-amber-500/20';
        } else if (bmi >= 18.5 && bmi < 25.0) {
            category = 'Normal';
            color = 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20';
        } else if (bmi >= 25.0 && bmi < 30.0) {
            category = 'Sobrepeso';
            color = 'text-amber-500 bg-amber-500/10 border-amber-500/20';
        } else if (bmi >= 30.0 && bmi < 35.0) {
            category = 'Obesidad I';
            color = 'text-rose-500 bg-rose-500/10 border-rose-500/20';
        } else {
            category = 'Obesidad II+';
            color = 'text-rose-600 bg-rose-600/10 border-rose-600/20';
        }

        const idealMin = 18.5 * (hM * hM);
        const idealMax = 24.9 * (hM * hM);

        return {
            bmi: bmi.toFixed(1),
            category,
            color,
            idealMin: idealMin.toFixed(1),
            idealMax: idealMax.toFixed(1),
        };
    }, [watchHeight, watchWeight]);

    // ── Polling logic for results ───────────────────────────────────────────
    useEffect(() => {
        let pollInterval: NodeJS.Timeout;

        if (step === 6 && resultData && !resultData.diagnosis) {
            setIsPolling(true);
            pollInterval = setInterval(async () => {
                try {
                    const { data } = await apiClient.get(`/wellness/evaluate/results/${resultData.id}`);
                    if (data.data.diagnosis) {
                        setResultData(data.data);
                        setIsPolling(false);
                        clearInterval(pollInterval);
                    }
                } catch (err) {
                    console.error('Polling error:', err);
                }
            }, 3000);
        }

        return () => {
            if (pollInterval) clearInterval(pollInterval);
        };
    }, [step, resultData?.id, resultData?.diagnosis]);

    // ── Symptom toggle helper ─────────────────────────────────────────────
    const toggleSymptom = (symptomKey: string) => {
        const label = t(`wellnessForm.${symptomKey}`);
        setSelectedSymptoms((prev) =>
            prev.includes(label) ? prev.filter((s) => s !== label) : [...prev, label]
        );
    };

    const isSymptomChecked = (symptomKey: string) =>
        selectedSymptoms.includes(t(`wellnessForm.${symptomKey}`));

    // ── Navigation ────────────────────────────────────────────────────────
    const nextStep = async () => {
        let fieldsToValidate: any[] = [];
        if (step === 1) fieldsToValidate = ['age', 'gender'];
        if (step === 2) fieldsToValidate = ['height_cm', 'weight_kg'];
        if (step === 4) fieldsToValidate = ['primary_goal', 'activity_level', 'meals_per_day'];

        if (fieldsToValidate.length > 0) {
            const isValid = await trigger(fieldsToValidate);
            if (!isValid) return;
        }
        setStep((s) => s + 1);
        if (typeof window !== 'undefined') window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    const prevStep = () => {
        setStep((s) => s - 1);
        if (typeof window !== 'undefined') window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    // ── Submit ────────────────────────────────────────────────────────────
    const onSubmit = async (values: EvaluationFormValues) => {
        setIsSubmitting(true);
        try {
            const payload = {
                ...values,
                age: Number(values.age),
                height_cm: Number(values.height_cm),
                weight_kg: Number(values.weight_kg),
                meals_per_day: Number(values.meals_per_day),
                pulse: values.pulse ? Number(values.pulse) : undefined,
                energy_level: values.energy_level ? Number(values.energy_level) : undefined,
                symptoms: selectedSymptoms,
                language: i18n.language,
            };
            const { data } = await apiClient.post(`/wellness/evaluate/${distributor_id}`, payload);
            setResultData(data.data);
            setStep(6);
            if (typeof window !== 'undefined') window.scrollTo({ top: 0, behavior: 'smooth' });
        } catch (err) {
            toast.error(t('common.error', { defaultValue: 'Submission failed. Please try again.' }));
        } finally {
            setIsSubmitting(false);
        }
    };

    const progress = (step / (TOTAL_STEPS - 2)) * 100;

    // ── Quick Goal Options ──────────────────────────────────────────────────
    const popularGoals = [
        { key: 'weight_loss', label: 'Perder Peso y Grasa', icon: '🔥' },
        { key: 'muscle_gain', label: 'Ganar Masa Muscular', icon: '💪' },
        { key: 'energy', label: 'Aumentar Energía y Vitalidad', icon: '⚡' },
        { key: 'wellness', label: 'Mejorar Digestión y Salud', icon: '🥗' },
        { key: 'healthy_aging', label: 'Bienestar y Nutrición Integral', icon: '✨' },
    ];

    // ── Results View ──────────────────────────────────────────────────────
    if (step === 6 && resultData) {
        return (
            <div className="mx-auto max-w-3xl px-4 py-8 md:py-12 space-y-6">
                {/* Header Card */}
                <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-emerald-600 via-teal-700 to-slate-900 p-6 md:p-8 text-white shadow-2xl">
                    <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                        <div className="space-y-2">
                            <div className="flex items-center gap-2">
                                <Badge className="bg-white/20 hover:bg-white/30 text-white border-none font-bold text-xs uppercase tracking-wider backdrop-blur-md">
                                    <Sparkles className="w-3.5 h-3.5 mr-1 text-emerald-300" />
                                    Diagnóstico Nutricional IA
                                </Badge>
                                <span className="text-xs text-white/80">
                                    {new Date().toLocaleDateString(i18n.language, { year: 'numeric', month: 'long', day: 'numeric' })}
                                </span>
                            </div>
                            <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight">
                                ¡Felicidades, {resultData.first_name || 'Prospecto'}!
                            </h1>
                            <p className="text-sm text-emerald-100 max-w-xl leading-relaxed">
                                Tu evaluación de bienestar ha sido procesada exitosamente por el motor de IA nutricional de EnpiAI para tu Coach <span className="font-bold underline">{profile?.name || 'Herbalife'}</span>.
                            </p>
                        </div>
                        <div className="shrink-0 flex items-center justify-center w-16 h-16 rounded-2xl bg-white/10 backdrop-blur-md border border-white/20 shadow-inner">
                            <Activity className="w-8 h-8 text-emerald-300 animate-pulse" />
                        </div>
                    </div>
                </div>

                {/* Main Content Card */}
                <Card className="rounded-3xl border-border/60 shadow-xl overflow-hidden backdrop-blur-sm">
                    <CardContent className="p-6 md:p-8 space-y-8">
                        {/* Vitals & Metrics Grid */}
                        <section className="space-y-4">
                            <h3 className="text-lg font-bold flex items-center gap-2 text-foreground">
                                <Scale className="w-5 h-5 text-emerald-500" />
                                {t('wellnessForm.measurementsResult', { defaultValue: 'Composición y Signos Vitales' })}
                            </h3>
                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5">
                                <div className="p-4 rounded-2xl bg-muted/40 border border-border/50 text-center space-y-1">
                                    <span className="text-xs text-muted-foreground font-medium">{t('wellnessForm.weight', { defaultValue: 'Peso' })}</span>
                                    <p className="text-xl font-extrabold text-foreground">{resultData.weight_kg} <span className="text-xs font-normal">kg</span></p>
                                </div>
                                <div className="p-4 rounded-2xl bg-muted/40 border border-border/50 text-center space-y-1">
                                    <span className="text-xs text-muted-foreground font-medium">{t('wellnessForm.height', { defaultValue: 'Estatura' })}</span>
                                    <p className="text-xl font-extrabold text-foreground">{resultData.height_cm} <span className="text-xs font-normal">cm</span></p>
                                </div>
                                <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-center space-y-1">
                                    <span className="text-xs text-emerald-600 dark:text-emerald-400 font-semibold">{t('wellnessForm.bmi', { defaultValue: 'IMC' })}</span>
                                    <p className="text-xl font-black text-emerald-600 dark:text-emerald-400">{resultData.bmi}</p>
                                </div>
                                <div className="p-4 rounded-2xl bg-muted/40 border border-border/50 text-center space-y-1">
                                    <span className="text-xs text-muted-foreground font-medium">{t('wellnessForm.bmiCategory', { defaultValue: 'Categoría' })}</span>
                                    <p className="text-sm font-bold text-foreground truncate">{resultData.bmi_category || 'Normal'}</p>
                                </div>
                            </div>

                            {(resultData.blood_pressure || resultData.pulse || resultData.energy_level) && (
                                <div className="grid grid-cols-3 gap-3 pt-2">
                                    {resultData.blood_pressure && (
                                        <div className="p-3 rounded-xl bg-muted/30 text-center text-xs">
                                            <span className="text-muted-foreground">{t('wellnessForm.bloodPressure', { defaultValue: 'Presión' })}:</span>
                                            <p className="font-bold text-foreground mt-0.5">{resultData.blood_pressure}</p>
                                        </div>
                                    )}
                                    {resultData.pulse && (
                                        <div className="p-3 rounded-xl bg-muted/30 text-center text-xs">
                                            <span className="text-muted-foreground">{t('wellnessForm.pulse', { defaultValue: 'Pulso' })}:</span>
                                            <p className="font-bold text-foreground mt-0.5">{resultData.pulse} bpm</p>
                                        </div>
                                    )}
                                    {resultData.energy_level && (
                                        <div className="p-3 rounded-xl bg-muted/30 text-center text-xs">
                                            <span className="text-muted-foreground">{t('wellnessForm.energyLevel', { defaultValue: 'Energía' })}:</span>
                                            <p className="font-bold text-foreground mt-0.5">{resultData.energy_level}/10 ⚡</p>
                                        </div>
                                    )}
                                </div>
                            )}
                        </section>

                        {/* Symptoms Reported */}
                        {resultData.symptoms && resultData.symptoms.length > 0 && (
                            <section className="space-y-3">
                                <h3 className="text-sm font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                                    <Heart className="w-4 h-4 text-rose-500" />
                                    {t('wellnessForm.reportedSymptoms', { defaultValue: 'Síntomas Reportados' })} ({resultData.symptoms.length})
                                </h3>
                                <div className="flex flex-wrap gap-2">
                                    {resultData.symptoms.map((s: string, idx: number) => (
                                        <Badge key={idx} variant="secondary" className="px-3 py-1 text-xs rounded-lg font-medium">
                                            {s}
                                        </Badge>
                                    ))}
                                </div>
                            </section>
                        )}

                        {/* AI Loading State or Results */}
                        {isPolling ? (
                            <div className="rounded-3xl border-2 border-dashed border-emerald-500/30 bg-emerald-500/5 p-8 text-center space-y-4">
                                <div className="relative mx-auto w-16 h-16 flex items-center justify-center">
                                    <div className="absolute inset-0 rounded-full bg-emerald-500/20 animate-ping" />
                                    <Loader2 className="h-8 w-8 animate-spin text-emerald-600 dark:text-emerald-400 relative z-10" />
                                </div>
                                <div className="space-y-1.5 max-w-md mx-auto">
                                    <h3 className="font-bold text-lg text-foreground">{t('wellnessForm.analyzingTitle', { defaultValue: 'Generando tu Diagnóstico Inteligente...' })}</h3>
                                    <p className="text-xs text-muted-foreground leading-relaxed">
                                        {t('wellnessForm.analyzingDesc', { defaultValue: 'Nuestra IA está calculando tus requerimientos calóricos, analizando síntomas y personalizando tu plan nutricional.' })}
                                    </p>
                                </div>
                            </div>
                        ) : (
                            <div className="space-y-6">
                                {/* AI Diagnosis */}
                                <div className="rounded-3xl border border-border/80 bg-muted/40 p-6 space-y-3 shadow-sm">
                                    <div className="flex items-center gap-2">
                                        <div className="w-8 h-8 rounded-xl bg-indigo-500/10 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
                                            <Bot className="w-4 h-4" />
                                        </div>
                                        <h3 className="font-bold text-base text-foreground">
                                            {t('wellnessForm.diagnosisTitle', { defaultValue: 'Diagnóstico Nutricional con IA' })}
                                        </h3>
                                    </div>
                                    <p className="text-sm leading-relaxed text-foreground/90 whitespace-pre-line">
                                        {resultData.diagnosis || t('wellnessForm.noDiagnosis', { defaultValue: 'Tu plan se está ajustando a tus requerimientos.' })}
                                    </p>
                                </div>

                                {/* AI Recommendations */}
                                <div className="rounded-3xl border border-emerald-500/30 bg-emerald-50 dark:bg-emerald-950/20 p-6 space-y-3 shadow-sm">
                                    <div className="flex items-center gap-2">
                                        <div className="w-8 h-8 rounded-xl bg-emerald-500/20 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
                                            <Sparkles className="w-4 h-4" />
                                        </div>
                                        <h3 className="font-bold text-base text-emerald-900 dark:text-emerald-300">
                                            {t('wellnessForm.recommendationsTitle', { defaultValue: 'Recomendaciones y Protocolo de Bienestar' })}
                                        </h3>
                                    </div>
                                    <p className="text-sm leading-relaxed text-emerald-950 dark:text-emerald-200/90 whitespace-pre-line">
                                        {resultData.recommendations || t('wellnessForm.noRecommendations', { defaultValue: 'Consulta con tu Coach para iniciar tu programa.' })}
                                    </p>
                                </div>
                            </div>
                        )}
                    </CardContent>

                    {/* Action & Sharing Footer */}
                    <CardFooter className="flex flex-col gap-6 p-6 md:p-8 bg-muted/20 border-t border-border/50">
                        <div className="flex flex-wrap items-center justify-center gap-3 w-full">
                            <Button 
                                variant="outline" 
                                onClick={() => window.location.reload()} 
                                className="rounded-xl flex-1 min-w-[140px]"
                            >
                                <ArrowLeft className="w-4 h-4 mr-2" />
                                {t('wellnessForm.startNew', { defaultValue: 'Nueva Evaluación' })}
                            </Button>
                            
                            {!isPolling && resultData.pdf_url && (
                                <Button 
                                    variant="default" 
                                    className="rounded-xl flex-1 min-w-[160px] bg-emerald-600 hover:bg-emerald-700 text-white shadow-lg shadow-emerald-600/20"
                                    onClick={() => window.open(resultData.pdf_url, '_blank')}
                                >
                                    <Download className="mr-2 h-4 w-4" /> {t('wellnessForm.downloadPDF', { defaultValue: 'Descargar Reporte PDF' })}
                                </Button>
                            )}

                            {!isPolling && (
                                <div className="flex gap-2">
                                    <Button 
                                        variant="outline" 
                                        className="rounded-xl border-green-500/30 hover:bg-green-500/10 text-green-600 dark:text-green-400"
                                        title={t('wellnessForm.shareViaWhatsApp', { defaultValue: 'Compartir en WhatsApp' })}
                                        onClick={() => {
                                            const baseUrl = typeof window !== 'undefined' ? window.location.origin : 'https://enpi.click';
                                            const pdfLink = resultData.pdf_url || `${baseUrl}/evaluate/${distributor_id}`;
                                            const shareMsg = `🌿 ¡Hola! Este es mi análisis de bienestar personalizado de EnpiAI: ${pdfLink}`;
                                            window.open(`https://wa.me/?text=${encodeURIComponent(shareMsg)}`, '_blank');
                                        }}
                                    >
                                        <MessageCircle className="h-4 w-4 mr-1.5" /> WhatsApp
                                    </Button>
                                    <Button 
                                        variant="outline" 
                                        className="rounded-xl border-blue-500/30 hover:bg-blue-500/10 text-blue-500"
                                        title={t('wellnessForm.shareViaTelegram', { defaultValue: 'Compartir en Telegram' })}
                                        onClick={() => {
                                            const baseUrl = typeof window !== 'undefined' ? window.location.origin : 'https://enpi.click';
                                            const pdfLink = resultData.pdf_url || `${baseUrl}/evaluate/${distributor_id}`;
                                            const shareMsg = `🌿 Mi análisis de bienestar:`;
                                            window.open(`https://t.me/share/url?url=${encodeURIComponent(pdfLink)}&text=${encodeURIComponent(shareMsg)}`, '_blank');
                                        }}
                                    >
                                        <Send className="h-4 w-4 mr-1.5" /> Telegram
                                    </Button>
                                </div>
                            )}
                        </div>

                        {/* Referral / Contact Coach Box */}
                        <div className="w-full rounded-2xl bg-gradient-to-r from-emerald-500/10 via-teal-500/10 to-indigo-500/10 border border-emerald-500/20 p-5 text-center space-y-3">
                            <div className="space-y-1">
                                <h4 className="font-bold text-base text-foreground flex items-center justify-center gap-1.5">
                                    <ShieldCheck className="w-4 h-4 text-emerald-500" />
                                    {t('wellnessForm.inviteTitle', { defaultValue: '¿Quieres que tu Coach te contacte?' })}
                                </h4>
                                <p className="text-xs text-muted-foreground max-w-md mx-auto">
                                    {t('wellnessForm.inviteSubtitle', { defaultValue: 'Tu Coach de Bienestar revisará tus resultados para ayudarte a elegir el plan ideal sin compromiso.' })}
                                </p>
                            </div>
                            <div className="flex flex-wrap justify-center gap-3 pt-1">
                                <Button 
                                    variant="outline" 
                                    size="sm"
                                    className="rounded-xl text-xs"
                                    onClick={() => {
                                        const distLink = typeof window !== 'undefined' ? `${window.location.origin}/evaluate/${distributor_id}` : `https://enpi.click/evaluate/${distributor_id}`;
                                        const text = encodeURIComponent(`¡Hola! Haz tu chequeo de bienestar gratuito con IA aquí: ${distLink}`);
                                        window.open(`https://wa.me/?text=${text}`, '_blank');
                                    }}
                                >
                                    <Share2 className="mr-1.5 h-3.5 w-3.5" /> {t('wellnessForm.inviteFriend', { defaultValue: 'Compartir con un Amigo' })}
                                </Button>
                            </div>
                        </div>
                    </CardFooter>
                </Card>
            </div>
        );
    }

    // ── Interactive Conversational Form Layout ──────────────────────────────
    return (
        <div className="mx-auto flex max-w-2xl flex-col px-4 py-8 md:py-12 space-y-6">
            {/* Top Bar: Coach Badge, Theme & Language */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-full bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-bold text-xs">
                        🌿
                    </div>
                    <div>
                        <p className="text-xs font-semibold text-foreground">{profile?.name || 'Coach de Bienestar'}</p>
                        <p className="text-[10px] text-muted-foreground">Distribuidor Independiente</p>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    <ThemeToggle />
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm" className="h-8 gap-1.5 text-muted-foreground hover:text-foreground text-xs rounded-xl">
                                <Languages className="h-3.5 w-3.5" />
                                <span className="font-semibold uppercase">{i18n.language}</span>
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => i18n.changeLanguage('es')}>
                                {t('wellnessForm.spanish', { defaultValue: 'Español' })}
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => i18n.changeLanguage('en')}>
                                {t('wellnessForm.english', { defaultValue: 'English' })}
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => i18n.changeLanguage('pt')}>
                                {t('wellnessForm.portuguese', { defaultValue: 'Português' })}
                            </DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>
                </div>
            </div>

            {/* Stepper Progress */}
            {step > 0 && (
                <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                            {t('wellnessForm.step', { defaultValue: 'Paso' })} {step} de {TOTAL_STEPS - 2}
                        </span>
                        <span>{Math.round(progress)}% Completado</span>
                    </div>
                    <Progress value={progress} className="h-2 rounded-full" />
                </div>
            )}

            {/* Conversational Assistant Bubble */}
            <div className="flex items-start gap-3 p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-foreground">
                <div className="w-8 h-8 rounded-full bg-emerald-500 text-white flex items-center justify-center shrink-0 shadow-md">
                    <Bot className="w-4 h-4" />
                </div>
                <div className="space-y-0.5 text-xs sm:text-sm">
                    <p className="font-bold text-emerald-950 dark:text-emerald-300">Asistente de Bienestar IA</p>
                    <p className="text-muted-foreground leading-relaxed">
                        {step === 0 && '¡Hola! Te ayudaré a calcular tu IMC, gasto calórico y plan nutricional personalizado en solo 2 minutos.'}
                        {step === 1 && 'Para comenzar con precisión, cuéntame tu edad y género biológico.'}
                        {step === 2 && 'Ingresa tu estatura y peso. Verás el cálculo de tu IMC en tiempo real.'}
                        {step === 3 && 'Selecciona cualquier molestia o síntoma para que la IA adapte tus nutrientes.'}
                        {step === 4 && '¿Cuáles son tus objetivos principales y ritmo de vida actual?'}
                        {step === 5 && '¡Último paso! ¿A qué WhatsApp o correo enviamos tu diagnóstico completo?'}
                    </p>
                </div>
            </div>

            {/* Form Card */}
            <Card className="rounded-3xl border-border/70 shadow-2xl overflow-hidden">
                <form onSubmit={handleSubmit(onSubmit)}>
                    {/* ═══════════════════════════════════════════════════════════
                        PASO 0: BIENVENIDA / INTRO
                    ═══════════════════════════════════════════════════════════ */}
                    {step === 0 && (
                        <>
                            <CardHeader className="text-center pb-2 pt-8">
                                <div className="mx-auto w-14 h-14 rounded-2xl bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mb-3">
                                    <Sparkles className="w-7 h-7" />
                                </div>
                                <CardTitle className="text-2xl sm:text-3xl font-extrabold tracking-tight">
                                    {t('wellnessForm.title', { defaultValue: 'Chequeo de Bienestar Gratuito' })}
                                </CardTitle>
                                <CardDescription className="text-sm max-w-md mx-auto pt-2">
                                    {t('wellnessForm.subtitle', { defaultValue: 'Obtén un análisis de salud personalizado y un plan de nutrición en menos de 2 minutos.' })}
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4 pt-6">
                                <div className="grid gap-3">
                                    <div className="flex items-center gap-3 p-3.5 rounded-2xl bg-muted/40 border border-border/50">
                                        <div className="w-8 h-8 rounded-xl bg-emerald-500/15 flex items-center justify-center text-emerald-600 dark:text-emerald-400 font-bold text-sm">
                                            📊
                                        </div>
                                        <div className="text-xs sm:text-sm">
                                            <p className="font-semibold">{t('wellnessForm.bullet1', { defaultValue: 'Cálculo del Índice de Masa Corporal (IMC)' })}</p>
                                            <p className="text-muted-foreground text-[11px]">Rango ideal de peso y requerimiento calórico</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-3 p-3.5 rounded-2xl bg-muted/40 border border-border/50">
                                        <div className="w-8 h-8 rounded-xl bg-indigo-500/15 flex items-center justify-center text-indigo-600 dark:text-indigo-400 font-bold text-sm">
                                            🧠
                                        </div>
                                        <div className="text-xs sm:text-sm">
                                            <p className="font-semibold">{t('wellnessForm.bullet2', { defaultValue: 'Diagnóstico de Salud con IA' })}</p>
                                            <p className="text-muted-foreground text-[11px]">Detección de patrones en energía, digestión y metabolismo</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-3 p-3.5 rounded-2xl bg-muted/40 border border-border/50">
                                        <div className="w-8 h-8 rounded-xl bg-amber-500/15 flex items-center justify-center text-amber-600 dark:text-amber-400 font-bold text-sm">
                                            🥗
                                        </div>
                                        <div className="text-xs sm:text-sm">
                                            <p className="font-semibold">{t('wellnessForm.bullet3', { defaultValue: 'Recomendaciones de Productos Personalizadas' })}</p>
                                            <p className="text-muted-foreground text-[11px]">Plan nutricional guiado por tu distribuidor oficial</p>
                                        </div>
                                    </div>
                                </div>
                            </CardContent>
                            <CardFooter className="pt-6 pb-8">
                                <Button 
                                    type="button" 
                                    onClick={() => setStep(1)} 
                                    className="w-full py-6 text-base font-bold rounded-2xl bg-emerald-600 hover:bg-emerald-700 text-white shadow-xl shadow-emerald-600/25"
                                >
                                    {t('wellnessForm.startNow', { defaultValue: 'Comenzar Mi Evaluación' })} <ArrowRight className="ml-2 h-5 w-5" />
                                </Button>
                            </CardFooter>
                        </>
                    )}

                    {/* ═══════════════════════════════════════════════════════════
                        PASO 1: PERFIL BÁSICO (EDAD Y GÉNERO)
                    ═══════════════════════════════════════════════════════════ */}
                    {step === 1 && (
                        <>
                            <CardHeader>
                                <CardTitle className="text-xl font-bold flex items-center gap-2">
                                    <User className="w-5 h-5 text-emerald-500" />
                                    {t('wellnessForm.aboutYou', { defaultValue: 'Sobre Ti' })}
                                </CardTitle>
                                <CardDescription>Datos clave para calcular tus tasas metabólicas.</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-6">
                                <div className="space-y-3">
                                    <Label className="text-sm font-semibold">{t('wellnessForm.gender', { defaultValue: 'Género Biológico' })}</Label>
                                    <div className="grid grid-cols-2 gap-3">
                                        <button
                                            type="button"
                                            onClick={() => setValue('gender', 'female')}
                                            className={`p-4 rounded-2xl border text-center transition-all flex flex-col items-center gap-2 cursor-pointer ${
                                                currentGender === 'female'
                                                    ? 'border-emerald-500 bg-emerald-500/10 shadow-md shadow-emerald-500/10 text-emerald-700 dark:text-emerald-300 font-bold'
                                                    : 'border-border/60 hover:bg-muted/50 text-muted-foreground'
                                            }`}
                                        >
                                            <span className="text-2xl">👩</span>
                                            <span className="text-sm">{t('wellnessForm.female', { defaultValue: 'Femenino' })}</span>
                                        </button>
                                        <button
                                            type="button"
                                            onClick={() => setValue('gender', 'male')}
                                            className={`p-4 rounded-2xl border text-center transition-all flex flex-col items-center gap-2 cursor-pointer ${
                                                currentGender === 'male'
                                                    ? 'border-emerald-500 bg-emerald-500/10 shadow-md shadow-emerald-500/10 text-emerald-700 dark:text-emerald-300 font-bold'
                                                    : 'border-border/60 hover:bg-muted/50 text-muted-foreground'
                                            }`}
                                        >
                                            <span className="text-2xl">👨</span>
                                            <span className="text-sm">{t('wellnessForm.male', { defaultValue: 'Masculino' })}</span>
                                        </button>
                                    </div>
                                    {errors.gender && <p className="text-xs text-destructive">{errors.gender.message}</p>}
                                </div>

                                <div className="space-y-2">
                                    <Label className="text-sm font-semibold">{t('wellnessForm.age', { defaultValue: 'Edad (Años)' })}</Label>
                                    <Input 
                                        type="number" 
                                        {...register('age')} 
                                        placeholder="Ej. 32" 
                                        className="h-12 rounded-xl text-base"
                                        onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); nextStep(); } }}
                                    />
                                    {errors.age && <p className="text-xs text-destructive">{errors.age.message}</p>}
                                </div>
                            </CardContent>
                            <CardFooter className="flex justify-between pt-6 border-t border-border/50">
                                <Button type="button" variant="outline" onClick={prevStep} className="rounded-xl">
                                    <ArrowLeft className="mr-1.5 h-4 w-4" /> {t('wellnessForm.back', { defaultValue: 'Atrás' })}
                                </Button>
                                <Button type="button" onClick={nextStep} className="rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white">
                                    {t('wellnessForm.next', { defaultValue: 'Continuar' })} <ArrowRight className="ml-1.5 h-4 w-4" />
                                </Button>
                            </CardFooter>
                        </>
                    )}

                    {/* ═══════════════════════════════════════════════════════════
                        PASO 2: MEDIDAS CORPORALES & IMC EN VIVO
                    ═══════════════════════════════════════════════════════════ */}
                    {step === 2 && (
                        <>
                            <CardHeader>
                                <CardTitle className="text-xl font-bold flex items-center gap-2">
                                    <Scale className="w-5 h-5 text-emerald-500" />
                                    {t('wellnessForm.measurements', { defaultValue: 'Medidas Corporales' })}
                                </CardTitle>
                                <CardDescription>Ingresa tu estatura y peso actual para calcular tu IMC.</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-6">
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label className="text-sm font-semibold">{t('wellnessForm.height', { defaultValue: 'Estatura (cm)' })}</Label>
                                        <Input 
                                            type="number" 
                                            {...register('height_cm')} 
                                            placeholder="170" 
                                            className="h-12 rounded-xl text-base"
                                        />
                                        {errors.height_cm && <p className="text-xs text-destructive">{errors.height_cm.message}</p>}
                                    </div>
                                    <div className="space-y-2">
                                        <Label className="text-sm font-semibold">{t('wellnessForm.weight', { defaultValue: 'Peso Actual (kg)' })}</Label>
                                        <Input 
                                            type="number" 
                                            {...register('weight_kg')} 
                                            placeholder="72" 
                                            className="h-12 rounded-xl text-base"
                                        />
                                        {errors.weight_kg && <p className="text-xs text-destructive">{errors.weight_kg.message}</p>}
                                    </div>
                                </div>

                                {/* Live BMI Gauge */}
                                {liveCalculations && (
                                    <div className={`p-4 rounded-2xl border transition-all ${liveCalculations.color} flex items-center justify-between`}>
                                        <div>
                                            <span className="text-xs uppercase font-bold tracking-wider">Tu IMC Estimado</span>
                                            <p className="text-2xl font-black">{liveCalculations.bmi} <span className="text-sm font-semibold">({liveCalculations.category})</span></p>
                                        </div>
                                        <div className="text-right text-xs">
                                            <span className="opacity-80">Rango ideal sugerido:</span>
                                            <p className="font-bold">{liveCalculations.idealMin} - {liveCalculations.idealMax} kg</p>
                                        </div>
                                    </div>
                                )}

                                {/* Energy Slider */}
                                <div className="space-y-3 pt-2">
                                    <div className="flex items-center justify-between">
                                        <Label className="text-sm font-semibold flex items-center gap-1.5">
                                            <Zap className="w-4 h-4 text-amber-500" />
                                            {t('wellnessForm.energyLevel', { defaultValue: '¿Cómo sientes tu nivel de energía habitual?' })}
                                        </Label>
                                        <span className="text-sm font-extrabold text-amber-500">{currentEnergy} / 10</span>
                                    </div>
                                    <input 
                                        type="range" 
                                        min="1" 
                                        max="10" 
                                        value={currentEnergy} 
                                        onChange={(e) => setValue('energy_level', e.target.value)}
                                        className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-emerald-500"
                                    />
                                    <div className="flex justify-between text-[11px] text-muted-foreground">
                                        <span>🔋 1-3 Cansado</span>
                                        <span>⚡ 4-7 Normal</span>
                                        <span>🚀 8-10 Con mucha energía</span>
                                    </div>
                                </div>

                                {/* Optional Vitals */}
                                <div className="grid grid-cols-2 gap-4 pt-2">
                                    <div className="space-y-1.5">
                                        <Label className="text-xs font-medium text-muted-foreground">
                                            {t('wellnessForm.bloodPressure', { defaultValue: 'Presión Arterial' })} <span className="text-[10px] uppercase">(Opcional)</span>
                                        </Label>
                                        <Input {...register('blood_pressure')} placeholder="Ej. 120/80" className="h-10 rounded-xl text-sm" />
                                    </div>
                                    <div className="space-y-1.5">
                                        <Label className="text-xs font-medium text-muted-foreground">
                                            {t('wellnessForm.pulse', { defaultValue: 'Pulso (lpm)' })} <span className="text-[10px] uppercase">(Opcional)</span>
                                        </Label>
                                        <Input type="number" {...register('pulse')} placeholder="Ej. 70" className="h-10 rounded-xl text-sm" />
                                    </div>
                                </div>
                            </CardContent>
                            <CardFooter className="flex justify-between pt-6 border-t border-border/50">
                                <Button type="button" variant="outline" onClick={prevStep} className="rounded-xl">
                                    <ArrowLeft className="mr-1.5 h-4 w-4" /> {t('wellnessForm.back', { defaultValue: 'Atrás' })}
                                </Button>
                                <Button type="button" onClick={nextStep} className="rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white">
                                    {t('wellnessForm.next', { defaultValue: 'Continuar' })} <ArrowRight className="ml-1.5 h-4 w-4" />
                                </Button>
                            </CardFooter>
                        </>
                    )}

                    {/* ═══════════════════════════════════════════════════════════
                        PASO 3: SÍNTOMAS Y CONDICIONES
                    ═══════════════════════════════════════════════════════════ */}
                    {step === 3 && (
                        <>
                            <CardHeader>
                                <div className="flex items-center justify-between">
                                    <CardTitle className="text-xl font-bold flex items-center gap-2">
                                        <Heart className="w-5 h-5 text-rose-500" />
                                        {t('wellnessForm.symptomsTitle', { defaultValue: 'Síntomas y Molestias' })}
                                    </CardTitle>
                                    <Badge variant="secondary" className="text-xs font-bold">
                                        {selectedSymptoms.length} seleccionados
                                    </Badge>
                                </div>
                                <CardDescription>Selecciona los síntomas frecuentes que experimentas.</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-5">
                                {/* Category Navigation Tabs */}
                                <div className="flex flex-wrap gap-1.5 p-1 rounded-2xl bg-muted/50 border border-border/40">
                                    {SYMPTOM_GROUPS.map((group) => (
                                        <button
                                            key={group.category}
                                            type="button"
                                            onClick={() => setActiveSymptomTab(group.category)}
                                            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
                                                activeSymptomTab === group.category
                                                    ? 'bg-background shadow text-emerald-600 dark:text-emerald-400'
                                                    : 'text-muted-foreground hover:text-foreground'
                                            }`}
                                        >
                                            <span>{group.icon}</span>
                                            <span>{t(`wellnessForm.${group.category}`, { defaultValue: group.category })}</span>
                                        </button>
                                    ))}
                                </div>

                                {/* Active Category Symptoms */}
                                {SYMPTOM_GROUPS.filter(g => g.category === activeSymptomTab).map((group) => (
                                    <div key={group.category} className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                                        {group.items.map((key) => {
                                            const checked = isSymptomChecked(key);
                                            return (
                                                <button
                                                    key={key}
                                                    type="button"
                                                    onClick={() => toggleSymptom(key)}
                                                    className={`p-3 rounded-2xl border text-left text-xs font-medium transition-all flex items-center justify-between gap-2 cursor-pointer ${
                                                        checked
                                                            ? 'border-emerald-500 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 font-bold shadow-sm'
                                                            : 'border-border/50 hover:bg-muted/40 text-foreground'
                                                    }`}
                                                >
                                                    <span>{t(`wellnessForm.${key}`)}</span>
                                                    <div className={`w-4 h-4 rounded-md border flex items-center justify-center shrink-0 ${
                                                        checked ? 'border-emerald-500 bg-emerald-500 text-white' : 'border-muted-foreground/30'
                                                    }`}>
                                                        {checked && <Check className="w-3 h-3" />}
                                                    </div>
                                                </button>
                                            );
                                        })}
                                    </div>
                                ))}
                            </CardContent>
                            <CardFooter className="flex justify-between pt-6 border-t border-border/50">
                                <Button type="button" variant="outline" onClick={prevStep} className="rounded-xl">
                                    <ArrowLeft className="mr-1.5 h-4 w-4" /> {t('wellnessForm.back', { defaultValue: 'Atrás' })}
                                </Button>
                                <Button type="button" onClick={nextStep} className="rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white">
                                    {t('wellnessForm.next', { defaultValue: 'Continuar' })} <ArrowRight className="ml-1.5 h-4 w-4" />
                                </Button>
                            </CardFooter>
                        </>
                    )}

                    {/* ═══════════════════════════════════════════════════════════
                        PASO 4: METAS Y HÁBITOS DE VIDA
                    ═══════════════════════════════════════════════════════════ */}
                    {step === 4 && (
                        <>
                            <CardHeader>
                                <CardTitle className="text-xl font-bold flex items-center gap-2">
                                    <Target className="w-5 h-5 text-emerald-500" />
                                    {t('wellnessForm.lifestyle', { defaultValue: 'Objetivos y Estilo de Vida' })}
                                </CardTitle>
                                <CardDescription>Para que el plan calce con tus tiempos y metas.</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-6">
                                {/* Primary Goal Pills */}
                                <div className="space-y-3">
                                    <Label className="text-sm font-semibold">{t('wellnessForm.primaryGoal', { defaultValue: '¿Cuál es tu objetivo principal?' })}</Label>
                                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                        {popularGoals.map((g) => (
                                            <button
                                                key={g.key}
                                                type="button"
                                                onClick={() => setValue('primary_goal', g.label)}
                                                className={`p-3 rounded-2xl border text-left text-xs font-semibold transition-all flex items-center gap-2.5 cursor-pointer ${
                                                    currentGoal === g.label
                                                        ? 'border-emerald-500 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 shadow-sm'
                                                        : 'border-border/60 hover:bg-muted/40 text-foreground'
                                                }`}
                                            >
                                                <span className="text-lg">{g.icon}</span>
                                                <span>{g.label}</span>
                                            </button>
                                        ))}
                                    </div>
                                    <Input 
                                        {...register('primary_goal')} 
                                        placeholder="O escribe tu objetivo personalizado..." 
                                        className="h-10 rounded-xl text-xs mt-2"
                                    />
                                    {errors.primary_goal && <p className="text-xs text-destructive">{errors.primary_goal.message}</p>}
                                </div>

                                {/* Activity Level */}
                                <div className="space-y-2">
                                    <Label className="text-sm font-semibold">{t('wellnessForm.activityLevel', { defaultValue: 'Nivel de Actividad Física' })}</Label>
                                    <select
                                        className="flex h-11 w-full rounded-xl border border-input bg-background px-3 py-2 text-sm shadow-sm"
                                        {...register('activity_level')}
                                    >
                                        <option value="sedentary">{t('wellnessForm.sedentary', { defaultValue: 'Sedentario (Poco o ningún ejercicio)' })}</option>
                                        <option value="light">{t('wellnessForm.light', { defaultValue: 'Ligero (Ejercicio 1-3 veces/semana)' })}</option>
                                        <option value="moderate">{t('wellnessForm.moderate', { defaultValue: 'Moderado (Ejercicio 4-5 veces/semana)' })}</option>
                                        <option value="active">{t('wellnessForm.active', { defaultValue: 'Activo (Ejercicio diario)' })}</option>
                                        <option value="very_active">{t('wellnessForm.veryActive', { defaultValue: 'Muy Activo (Ejercicio intenso/atletas)' })}</option>
                                    </select>
                                </div>

                                {/* Water and Meals */}
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label className="text-xs font-semibold flex items-center gap-1">
                                            <Droplets className="w-3.5 h-3.5 text-blue-500" />
                                            {t('wellnessForm.waterIntake', { defaultValue: 'Agua al día (Litros)' })}
                                        </Label>
                                        <Input type="number" step="0.1" {...register('water_intake_liters')} placeholder="2.0" className="h-11 rounded-xl text-sm" />
                                    </div>
                                    <div className="space-y-2">
                                        <Label className="text-xs font-semibold flex items-center gap-1">
                                            <span>🍽️</span>
                                            {t('wellnessForm.mealsPerDay', { defaultValue: 'Comidas al día' })}
                                        </Label>
                                        <Input type="number" {...register('meals_per_day')} placeholder="3" className="h-11 rounded-xl text-sm" />
                                    </div>
                                </div>

                                {/* Sleep Quality */}
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label className="text-xs font-semibold flex items-center gap-1">
                                            <Moon className="w-3.5 h-3.5 text-indigo-400" />
                                            {t('wellnessForm.sleepHours', { defaultValue: 'Horas de sueño' })}
                                        </Label>
                                        <Input type="number" {...register('sleep_hours')} placeholder="7" className="h-11 rounded-xl text-sm" />
                                    </div>
                                    <div className="space-y-2">
                                        <Label className="text-xs font-semibold">
                                            {t('wellnessForm.sleepQuality', { defaultValue: 'Calidad de sueño' })}
                                        </Label>
                                        <select
                                            className="flex h-11 w-full rounded-xl border border-input bg-background px-3 py-2 text-sm shadow-sm"
                                            {...register('sleep_quality')}
                                        >
                                            <option value="excellent">Excelente 😴</option>
                                            <option value="good">Buena 🙂</option>
                                            <option value="fair">Regular 😐</option>
                                            <option value="poor">Mala / Insomnio 😫</option>
                                        </select>
                                    </div>
                                </div>
                            </CardContent>
                            <CardFooter className="flex justify-between pt-6 border-t border-border/50">
                                <Button type="button" variant="outline" onClick={prevStep} className="rounded-xl">
                                    <ArrowLeft className="mr-1.5 h-4 w-4" /> {t('wellnessForm.back', { defaultValue: 'Atrás' })}
                                </Button>
                                <Button type="button" onClick={nextStep} className="rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white">
                                    {t('wellnessForm.next', { defaultValue: 'Continuar' })} <ArrowRight className="ml-1.5 h-4 w-4" />
                                </Button>
                            </CardFooter>
                        </>
                    )}

                    {/* ═══════════════════════════════════════════════════════════
                        PASO 5: DATOS DE CONTACTO Y ENTREGA
                    ═══════════════════════════════════════════════════════════ */}
                    {step === 5 && (
                        <>
                            <CardHeader>
                                <CardTitle className="text-xl font-bold flex items-center gap-2">
                                    <Sparkles className="w-5 h-5 text-emerald-500" />
                                    {t('wellnessForm.almostDone', { defaultValue: '¡Casi listo para tu Diagnóstico!' })}
                                </CardTitle>
                                <CardDescription>
                                    {t('wellnessForm.whereToSend', { defaultValue: 'Indícanos tus datos para entregarte el reporte detallado y conectar con tu Coach.' })}
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="space-y-2">
                                    <Label className="text-sm font-semibold">{t('wellnessForm.firstName', { defaultValue: 'Tu Nombre Completo' })}</Label>
                                    <Input {...register('first_name')} placeholder="Ej. Mariana Gómez" className="h-12 rounded-xl text-base" />
                                    {errors.first_name && <p className="text-xs text-destructive">{errors.first_name.message}</p>}
                                </div>
                                <div className="space-y-2">
                                    <Label className="text-sm font-semibold">{t('wellnessForm.email', { defaultValue: 'Correo Electrónico' })}</Label>
                                    <Input type="email" {...register('email')} placeholder="mariana@gmail.com" className="h-12 rounded-xl text-base" />
                                    {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
                                </div>
                                <div className="space-y-2">
                                    <Label className="text-sm font-semibold">{t('wellnessForm.phone', { defaultValue: 'Teléfono / WhatsApp' })}</Label>
                                    <Input type="tel" {...register('phone')} placeholder="+593 98 765 4321" className="h-12 rounded-xl text-base" />
                                    {errors.phone && <p className="text-xs text-destructive">{errors.phone.message}</p>}
                                </div>
                            </CardContent>
                            <CardFooter className="flex justify-between pt-6 border-t border-border/50">
                                <Button type="button" variant="outline" onClick={prevStep} className="rounded-xl">
                                    <ArrowLeft className="mr-1.5 h-4 w-4" /> {t('wellnessForm.back', { defaultValue: 'Atrás' })}
                                </Button>
                                <Button 
                                    type="submit" 
                                    disabled={isSubmitting} 
                                    className="rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-6 px-6 shadow-xl shadow-emerald-600/20 cursor-pointer"
                                >
                                    {isSubmitting ? (
                                        <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> {t('wellnessForm.analyzing', { defaultValue: 'Generando Diagnóstico...' })}</>
                                    ) : (
                                        <>{t('wellnessForm.getResults', { defaultValue: 'Ver Mi Diagnóstico Ahora' })} <ArrowRight className="ml-2 h-4 w-4" /></>
                                    )}
                                </Button>
                            </CardFooter>
                        </>
                    )}
                </form>
            </Card>
        </div>
    );
}
