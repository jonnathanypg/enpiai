'use client';

import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Check, ShieldCheck, Loader2, CreditCard, Sparkles } from 'lucide-react';
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
import { toast } from 'sonner';
import type { Plan } from '@/types';

export default function SubscribePage() {
    const [selectedPlanId, setSelectedPlanId] = useState<number | null>(null);

    const { data: plans = [], isLoading, error } = useQuery({
        queryKey: ['billing-plans'],
        queryFn: async () => {
            const { data } = await apiClient.get('/billing/plans');
            // The API returns an array directly
            return (Array.isArray(data) ? data : data?.data || []) as Plan[];
        },
        retry: 1,
    });

    const subscribeMutation = useMutation({
        mutationFn: async (planId: number) => {
            const { data } = await apiClient.post('/billing/subscribe', {
                plan_id: planId,
            });
            return data;
        },
        onSuccess: (data) => {
            if (data.subscribe_url) {
                toast.success('Redirigiendo a la pasarela de pago...');
                window.location.href = data.subscribe_url;
            } else {
                toast.error('No se pudo generar la URL de pago. Contacta al administrador.');
            }
        },
        onError: (error: any) => {
            toast.error(error?.response?.data?.error || 'Error al iniciar el proceso de suscripción.');
        },
    });

    const handleSubscribe = (planId: number) => {
        setSelectedPlanId(planId);
        subscribeMutation.mutate(planId);
    };

    if (isLoading) {
        return (
            <div className="flex h-[60vh] items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    return (
        <div className="mx-auto max-w-5xl space-y-8 py-8">
            {/* Header */}
            <div className="text-center space-y-3">
                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-primary/20 to-primary/5">
                    <Sparkles className="h-7 w-7 text-primary" />
                </div>
                <h1 className="text-4xl font-bold tracking-tight">
                    Activa tu Licencia
                </h1>
                <p className="text-lg text-muted-foreground max-w-xl mx-auto">
                    Para acceder a todas las herramientas de automatización, CRM e Inteligencia Artificial,
                    selecciona el plan que mejor se adapte a tu negocio.
                </p>
            </div>

            {/* Plans Grid */}
            {plans.length > 0 ? (
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                    {plans.map((plan) => (
                        <Card
                            key={plan.id}
                            className="flex flex-col relative overflow-hidden border-2 hover:border-primary/50 transition-colors"
                        >
                            {plan.is_default && (
                                <Badge className="absolute top-3 right-3">Recomendado</Badge>
                            )}
                            <CardHeader>
                                <CardTitle className="text-xl">{plan.name}</CardTitle>
                                <CardDescription>{plan.description}</CardDescription>
                            </CardHeader>
                            <CardContent className="flex-1">
                                <div className="mb-6 flex items-baseline gap-1">
                                    <span className="text-4xl font-bold">
                                        ${plan.price_monthly}
                                    </span>
                                    <span className="text-sm text-muted-foreground">
                                        {plan.currency} / mes
                                    </span>
                                </div>
                                {plan.features && (
                                    <ul className="space-y-2.5">
                                        {Object.entries(plan.features).map(([key, value]) => (
                                            <li key={key} className="flex items-center text-sm">
                                                <Check className="mr-2 h-4 w-4 text-green-500 shrink-0" />
                                                <span className="capitalize">
                                                    {key.replace(/_/g, ' ')}: {String(value)}
                                                </span>
                                            </li>
                                        ))}
                                    </ul>
                                )}
                            </CardContent>
                            <CardFooter>
                                <Button
                                    className="w-full"
                                    size="lg"
                                    onClick={() => handleSubscribe(plan.id)}
                                    disabled={subscribeMutation.isPending && selectedPlanId === plan.id}
                                >
                                    {subscribeMutation.isPending && selectedPlanId === plan.id ? (
                                        <>
                                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                            Redirigiendo...
                                        </>
                                    ) : (
                                        <>
                                            <CreditCard className="mr-2 h-4 w-4" />
                                            Suscribirse
                                        </>
                                    )}
                                </Button>
                            </CardFooter>
                        </Card>
                    ))}
                </div>
            ) : (
                <Card className="p-12 text-center">
                    <p className="text-muted-foreground text-lg">
                        No hay planes disponibles en este momento. Contacta al administrador de la plataforma.
                    </p>
                </Card>
            )}

            {/* Security Footer */}
            <Card className="bg-gradient-to-br from-primary/5 via-transparent to-transparent">
                <CardContent className="flex flex-col items-center gap-6 p-8 md:flex-row md:items-start md:text-left">
                    <div className="rounded-full bg-primary/10 p-4 shrink-0">
                        <ShieldCheck className="h-8 w-8 text-primary" />
                    </div>
                    <div className="space-y-2">
                        <h3 className="text-lg font-semibold">Pago Seguro con dLocal Go</h3>
                        <p className="text-muted-foreground">
                            Todos los pagos son procesados de forma segura a través de dLocal Go, la pasarela de pagos líder en Latinoamérica.
                            Tu información financiera nunca se almacena en nuestros servidores.
                        </p>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
