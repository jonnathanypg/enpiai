'use client';

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Bot, Sparkles, ArrowRight, Play, X, Check, Activity, FileText, MessageSquare, Radio } from 'lucide-react';
import { useOnboardingStore } from '@/store/use-onboarding-store';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

export function OnboardingDashboardBanner() {
    const { t } = useTranslation();
    const { completedSteps, startTour } = useOnboardingStore();
    const [dismissed, setDismissed] = useState(false);
    
    useEffect(() => {
        const value = localStorage.getItem('enpiai-onboarding-banner-dismissed');
        if (value === 'true') {
            setDismissed(true);
        }
    }, []);

    const handleDismiss = () => {
        localStorage.setItem('enpiai-onboarding-banner-dismissed', 'true');
        setDismissed(true);
    };

    if (dismissed) return null;

    const totalSteps = 5;
    const completedCount = ['agent', 'channel', 'document', 'wellness', 'coach'].filter(
        step => completedSteps.includes(step)
    ).length;
    const progressPercent = Math.round((completedCount / totalSteps) * 100);
    const isFinished = completedCount === totalSteps;

    return (
        <Card className="relative overflow-hidden border-none rounded-3xl bg-gradient-to-r from-emerald-950 via-teal-950 to-slate-950 text-white p-6 md:p-8 shadow-2xl transition-all duration-300">
            {/* Background glowing effects */}
            <div className="absolute right-0 top-0 w-80 h-full opacity-20 pointer-events-none bg-[radial-gradient(circle_at_top_right,rgba(16,185,129,0.5),transparent_70%)]" />
            <div className="absolute left-1/3 -bottom-10 w-60 h-40 opacity-15 pointer-events-none bg-emerald-500 rounded-full blur-3xl" />
            
            <button 
                onClick={handleDismiss}
                className="absolute right-4 top-4 p-1.5 rounded-full text-white/50 hover:text-white hover:bg-white/10 transition-colors cursor-pointer z-20"
                title="Ocultar guía"
            >
                <X className="h-4 w-4" />
            </button>

            <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
                {/* Greeting & Info */}
                <div className="space-y-3 max-w-xl">
                    <div className="flex items-center gap-2">
                        <span className="flex h-6 items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-emerald-300 bg-emerald-500/20 px-2.5 py-0.5 rounded-full border border-emerald-500/30">
                            <Sparkles className="h-3 w-3 text-emerald-400" />
                            Guía de Aceleración Herbalife
                        </span>
                        <span className="text-xs text-white/70">
                            {completedCount} de {totalSteps} tareas listas
                        </span>
                    </div>

                    <div className="space-y-1.5">
                        <h3 className="text-xl md:text-2xl font-black tracking-tight text-white">
                            {isFinished 
                                ? '¡Excelente! Tu Ecosistema de Distribuidor IA está 100% Activo' 
                                : 'Activa tu Asistente Nutricional y Encuestas de Bienestar'
                            }
                        </h3>
                        <p className="text-xs sm:text-sm text-emerald-100/80 leading-relaxed">
                            {isFinished 
                                ? 'Has habilitado las capacidades completas: calificación de prospectos, WhatsApp automatizado, base de productos y diagnósticos con IA.'
                                : 'Configura tu asistente para automatizar la atención en WhatsApp, captar clientes mediante el chequeo de bienestar y duplicar tus ventas.'
                            }
                        </p>
                    </div>

                    {!isFinished && (
                        <div className="flex flex-wrap gap-2 pt-1 text-xs">
                            <Link href="/agents" className="flex items-center gap-1.5 bg-white/10 hover:bg-white/20 px-3 py-1.5 rounded-xl transition-colors text-white">
                                {completedSteps.includes('agent') ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <div className="h-1.5 w-1.5 rounded-full bg-white" />}
                                Configurar Asistente
                            </Link>
                            <Link href="/channels" className="flex items-center gap-1.5 bg-white/10 hover:bg-white/20 px-3 py-1.5 rounded-xl transition-colors text-white">
                                {completedSteps.includes('channel') ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <div className="h-1.5 w-1.5 rounded-full bg-white" />}
                                Conectar WhatsApp
                            </Link>
                            <Link href="/wellness" className="flex items-center gap-1.5 bg-white/10 hover:bg-white/20 px-3 py-1.5 rounded-xl transition-colors text-white">
                                {completedSteps.includes('wellness') ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <div className="h-1.5 w-1.5 rounded-full bg-white" />}
                                Encuesta de Bienestar
                            </Link>
                            <Link href="/documents" className="flex items-center gap-1.5 bg-white/10 hover:bg-white/20 px-3 py-1.5 rounded-xl transition-colors text-white">
                                {completedSteps.includes('document') ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <div className="h-1.5 w-1.5 rounded-full bg-white" />}
                                Subir Catálogo
                            </Link>
                        </div>
                    )}
                </div>

                {/* Progress Circle & Tour Action */}
                <div className="flex flex-row md:flex-col items-center gap-4 w-full md:w-auto shrink-0 border-t md:border-t-0 border-white/10 pt-4 md:pt-0">
                    <div className="flex items-center gap-4">
                        <div className="relative w-16 h-16 flex items-center justify-center">
                            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                                <path
                                    className="text-white/10"
                                    strokeWidth="3.5"
                                    stroke="currentColor"
                                    fill="none"
                                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                                />
                                <path
                                    className="text-emerald-400 transition-all duration-700 ease-out"
                                    strokeDasharray={`${progressPercent}, 100`}
                                    strokeWidth="3.5"
                                    strokeLinecap="round"
                                    stroke="currentColor"
                                    fill="none"
                                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                                />
                            </svg>
                            <span className="absolute text-xs font-bold text-white">{progressPercent}%</span>
                        </div>

                        <Button 
                            onClick={() => startTour(0)}
                            className="bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold rounded-2xl text-xs px-4 py-5 shadow-lg shadow-emerald-500/20"
                        >
                            <Play className="h-3.5 w-3.5 mr-1.5 fill-current" />
                            Ver Tour Guiado
                        </Button>
                    </div>
                </div>
            </div>
        </Card>
    );
}
