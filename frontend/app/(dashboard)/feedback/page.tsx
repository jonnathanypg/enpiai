'use client';

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { Star, MessageSquareCode, Send, Sparkles, ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import apiClient from '@/lib/api-client';
import { cn } from '@/lib/utils';

export default function FeedbackPage() {
    const router = useRouter();
    const queryClient = useQueryClient();

    const [step, setStep] = useState<number>(1);
    const [rating, setRating] = useState<number>(0);
    const [hoverRating, setHoverRating] = useState<number>(0);
    const [q1, setQ1] = useState<string>('');
    const [q2, setQ2] = useState<string>('');
    const [q3, setQ3] = useState<string>('');
    const [comments, setComments] = useState<string>('');

    const feedbackMutation = useMutation({
        mutationFn: async (payload: any) => {
            const { data } = await apiClient.post('/distributors/submit-feedback', payload);
            return data;
        },
        onSuccess: () => {
            toast.success('¡Muchas gracias por tu retroalimentación! Redirigiendo a planes de suscripción...');
            queryClient.invalidateQueries({ queryKey: ['me'] });
            router.push('/subscribe');
        },
        onError: (error: any) => {
            const message = error?.response?.data?.error || 'Ocurrió un error al enviar el feedback. Inténtalo de nuevo.';
            toast.error(message);
        }
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (rating === 0) {
            toast.warning('Por favor, selecciona una calificación de estrellas.');
            setStep(1);
            return;
        }
        if (!q1 || !q2 || !q3) {
            toast.warning('Por favor, responde a todas las preguntas de usabilidad.');
            setStep(2);
            return;
        }

        feedbackMutation.mutate({
            rating,
            answers: {
                usability_ease: q1,
                most_useful_tool: q2,
                business_impact: q3
            },
            comments
        });
    };

    const nextStep = () => {
        if (step === 1 && rating === 0) {
            toast.warning('Por favor, selecciona una calificación antes de continuar.');
            return;
        }
        if (step === 2 && (!q1 || !q2 || !q3)) {
            toast.warning('Por favor, responde a las 3 preguntas antes de continuar.');
            return;
        }
        setStep((prev) => prev + 1);
    };

    const prevStep = () => {
        setStep((prev) => prev - 1);
    };

    const steps = [
        { id: 1, label: 'Experiencia', icon: Star },
        { id: 2, label: 'Preguntas', icon: MessageSquareCode },
        { id: 3, label: 'Sugerencias', icon: Sparkles }
    ];

    const isStep2Complete = q1 && q2 && q3;

    return (
        <div className="flex min-h-[calc(100vh-8rem)] items-center justify-center p-4">
            <style>{`
                @keyframes stepIn {
                    from {
                        opacity: 0;
                        transform: translateY(12px) scale(0.98);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0) scale(1);
                    }
                }
                @keyframes pulseGlow {
                    0%, 100% {
                        box-shadow: 0 0 0 0 rgba(112, 180, 50, 0.4);
                    }
                    50% {
                        box-shadow: 0 0 16px 4px rgba(112, 180, 50, 0.2);
                    }
                }
                .pulse-glow {
                    animation: pulseGlow 2s infinite;
                }
                .step-enter-active {
                    animation: stepIn 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards;
                }
            `}</style>

            <Card className="w-full max-w-2xl shadow-2xl border-primary/20 bg-background/60 backdrop-blur-md overflow-hidden transition-all duration-300">
                <CardHeader className="text-center pb-4 border-b border-border/20">
                    <div className="mx-auto h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center mb-2">
                        <MessageSquareCode className="h-6 w-6 text-primary animate-pulse" />
                    </div>
                    <CardTitle className="text-2xl font-bold flex items-center justify-center gap-2">
                        <Sparkles className="h-5 w-5 text-primary" />
                        Tu Opinión nos Ayuda a Crecer
                    </CardTitle>
                    <CardDescription className="text-sm mt-1 max-w-md mx-auto">
                        Tu prueba gratuita de 24 horas ha concluido. Ayúdanos a mejorar EnpiAI respondiendo a estas breves preguntas antes de contratar tu plan.
                    </CardDescription>
                </CardHeader>

                <div className="pt-6">
                    {/* Stepper progress indicator */}
                    <div className="flex items-center justify-between max-w-md mx-auto mb-6 relative px-8">
                        {/* Progress Line */}
                        <div className="absolute left-16 right-16 top-5 h-[2px] bg-muted/60 -z-10">
                            <div 
                                className="h-full bg-primary transition-all duration-500 ease-out"
                                style={{ width: `${((step - 1) / (steps.length - 1)) * 100}%` }}
                            />
                        </div>

                        {steps.map((s) => {
                            const Icon = s.icon;
                            const isActive = step === s.id;
                            const isCompleted = step > s.id;
                            
                            return (
                                <div key={s.id} className="flex flex-col items-center gap-1.5 z-10">
                                    <button
                                        type="button"
                                        onClick={() => {
                                            // Only allow navigation to completed steps or current step
                                            if (s.id < step) {
                                                setStep(s.id);
                                            } else if (s.id === 2 && rating > 0) {
                                                setStep(2);
                                            } else if (s.id === 3 && rating > 0 && isStep2Complete) {
                                                setStep(3);
                                            }
                                        }}
                                        disabled={s.id > step && (s.id === 2 ? rating === 0 : (rating === 0 || !isStep2Complete))}
                                        className={cn(
                                            "h-10 w-10 rounded-full flex items-center justify-center border-2 transition-all duration-300 cursor-pointer disabled:cursor-not-allowed",
                                            isCompleted 
                                                ? "bg-primary border-primary text-primary-foreground scale-105" 
                                                : isActive
                                                    ? "bg-background border-primary text-primary shadow-[0_0_12px_rgba(112,180,50,0.4)] scale-110"
                                                    : "bg-muted border-muted-foreground/30 text-muted-foreground hover:border-muted-foreground/60"
                                        )}
                                    >
                                        <Icon className="h-5 w-5" />
                                    </button>
                                    <span className={cn(
                                        "text-xs font-semibold select-none transition-colors",
                                        isActive ? "text-primary font-bold" : "text-muted-foreground"
                                    )}>
                                        {s.label}
                                    </span>
                                </div>
                            );
                        })}
                    </div>
                </div>

                <form onSubmit={handleSubmit}>
                    <CardContent className="min-h-[280px] flex flex-col justify-center px-8 py-6">
                        {/* STEP 1: Star Rating */}
                        {step === 1 && (
                            <div className="step-enter-active space-y-6 text-center">
                                <div className="space-y-2">
                                    <Label className="text-lg font-semibold block text-foreground">
                                        ¿Cómo calificarías tu experiencia general con EnpiAI?
                                    </Label>
                                    <p className="text-xs text-muted-foreground">
                                        Selecciona la cantidad de estrellas según tu nivel de satisfacción.
                                    </p>
                                </div>
                                <div className="flex justify-center gap-3 py-4">
                                    {[1, 2, 3, 4, 5].map((star) => (
                                        <button
                                            key={star}
                                            type="button"
                                            className="focus:outline-none transition-all duration-200 hover:scale-125 active:scale-90 p-1 cursor-pointer"
                                            onClick={() => {
                                                setRating(star);
                                                // Smooth delay transition to next step automatically
                                                setTimeout(() => {
                                                    setStep(2);
                                                }, 400);
                                            }}
                                            onMouseEnter={() => setHoverRating(star)}
                                            onMouseLeave={() => setHoverRating(0)}
                                        >
                                            <Star
                                                className={cn(
                                                    "h-12 w-12 transition-all duration-300 drop-shadow-md",
                                                    star <= (hoverRating || rating)
                                                        ? "fill-primary text-primary scale-105 filter drop-shadow-[0_0_6px_rgba(112,180,50,0.5)]"
                                                        : "text-muted-foreground/40"
                                                )}
                                            />
                                        </button>
                                    ))}
                                </div>
                                {rating > 0 && (
                                    <div className="text-sm font-medium text-primary animate-bounce">
                                        ¡Calificado con {rating} {rating === 1 ? 'estrella' : 'estrellas'}! Avanzando...
                                    </div>
                                )}
                            </div>
                        )}

                        {/* STEP 2: Usability Questions */}
                        {step === 2 && (
                            <div className="step-enter-active space-y-5">
                                <div className="space-y-1">
                                    <h3 className="text-base font-semibold text-foreground">Preguntas de Usabilidad</h3>
                                    <p className="text-xs text-muted-foreground">Por favor, responde a todas las preguntas para habilitar el siguiente paso.</p>
                                </div>

                                <div className="space-y-4">
                                    <div className="space-y-1.5">
                                        <Label htmlFor="q1" className="font-medium text-sm text-foreground/90 block">
                                            1. ¿Qué tan fácil de usar te resultó la plataforma EnpiAI?
                                        </Label>
                                        <select
                                            id="q1"
                                            className="flex h-10 w-full rounded-md border border-input bg-background/50 px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
                                            value={q1}
                                            onChange={(e) => setQ1(e.target.value)}
                                        >
                                            <option value="" disabled>Selecciona una opción</option>
                                            <option value="Muy Fácil">Muy Fácil - Todo es muy intuitivo</option>
                                            <option value="Fácil">Fácil - Se aprende rápido</option>
                                            <option value="Regular">Regular - Requiere práctica</option>
                                            <option value="Difícil">Difícil - Algo confuso</option>
                                        </select>
                                    </div>

                                    <div className="space-y-1.5">
                                        <Label htmlFor="q2" className="font-medium text-sm text-foreground/90 block">
                                            2. ¿Qué herramienta del sistema consideras que aporta más valor a tu negocio?
                                        </Label>
                                        <select
                                            id="q2"
                                            className="flex h-10 w-full rounded-md border border-input bg-background/50 px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
                                            value={q2}
                                            onChange={(e) => setQ2(e.target.value)}
                                        >
                                            <option value="" disabled>Selecciona una opción</option>
                                            <option value="Asistente de IA">Asistente de IA (Chat y Respuestas)</option>
                                            <option value="Canal WhatsApp/Telegram">Conexión de WhatsApp/Telegram Bot</option>
                                            <option value="Evaluaciones de Bienestar">Evaluaciones de Bienestar</option>
                                            <option value="Modo Coach">Modo Coach (Tareas diarias y motivación)</option>
                                            <option value="Todo">Todas las herramientas aportan valor</option>
                                        </select>
                                    </div>

                                    <div className="space-y-1.5">
                                        <Label htmlFor="q3" className="font-medium text-sm text-foreground/90 block">
                                            3. ¿Consideras que esta herramienta te ayudará a duplicar tus ventas y prospección en Herbalife?
                                        </Label>
                                        <select
                                            id="q3"
                                            className="flex h-10 w-full rounded-md border border-input bg-background/50 px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
                                            value={q3}
                                            onChange={(e) => setQ3(e.target.value)}
                                        >
                                            <option value="" disabled>Selecciona una opción</option>
                                            <option value="Sí, definitivamente">Sí, definitivamente - Agiliza mucho el trabajo</option>
                                            <option value="Tal vez">Tal vez - Con el uso continuo</option>
                                            <option value="No estoy seguro">No estoy seguro aún</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* STEP 3: Written comments */}
                        {step === 3 && (
                            <div className="step-enter-active space-y-4">
                                <div className="space-y-1">
                                    <Label htmlFor="comments" className="text-base font-semibold block text-foreground">
                                        Retroalimentación o sugerencia adicional (opcional)
                                    </Label>
                                    <p className="text-xs text-muted-foreground">
                                        ¿Hay algo más que desees compartir sobre tu experiencia o alguna mejora específica?
                                    </p>
                                </div>
                                <div className="space-y-2">
                                    <Textarea
                                        id="comments"
                                        placeholder="Dinos qué podemos mejorar o qué funcionalidades adicionales te gustarían..."
                                        value={comments}
                                        onChange={(e) => setComments(e.target.value)}
                                        className="min-h-[140px] bg-background/50 border-border focus:ring-2 focus:ring-primary/50 transition-all resize-none"
                                    />
                                </div>
                            </div>
                        )}
                    </CardContent>

                    <CardFooter className="border-t border-border/20 p-6 flex items-center justify-between">
                        {/* Back Button */}
                        <Button
                            type="button"
                            variant="outline"
                            onClick={prevStep}
                            disabled={step === 1}
                            className={cn(
                                "gap-1 transition-all",
                                step === 1 ? "opacity-0 pointer-events-none" : "opacity-100"
                            )}
                        >
                            <ChevronLeft className="h-4 w-4" />
                            Atrás
                        </Button>

                        {/* Next / Submit Button */}
                        {step < 3 ? (
                            <Button
                                type="button"
                                onClick={nextStep}
                                disabled={step === 1 ? rating === 0 : !isStep2Complete}
                                className={cn(
                                    "gap-1 transition-all duration-300",
                                    step === 2 && isStep2Complete ? "bg-primary text-primary-foreground pulse-glow scale-[1.02]" : ""
                                )}
                            >
                                Siguiente
                                <ChevronRight className="h-4 w-4" />
                            </Button>
                        ) : (
                            <Button
                                type="submit"
                                size="lg"
                                className="w-full sm:w-auto px-6 py-6 shadow-md hover:scale-[1.01] active:scale-[0.99] transition-all duration-300 bg-primary hover:bg-primary/90 text-primary-foreground"
                                disabled={feedbackMutation.isPending}
                            >
                                {feedbackMutation.isPending ? 'Enviando...' : 'Enviar y ver precios'}
                                <Send className="ml-2 h-4 w-4" />
                            </Button>
                        )}
                    </CardFooter>
                </form>
            </Card>
        </div>
    );
}
