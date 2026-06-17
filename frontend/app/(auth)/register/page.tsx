'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'sonner';
import { GoogleLogin } from '@react-oauth/google';
import { useTranslation } from 'react-i18next';
import { Sparkles } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from '@/components/ui/card';
import { useAuthStore } from '@/store/use-auth-store';
import apiClient from '@/lib/api-client';
import type { AuthResponse } from '@/types';

const registerSchema = z.object({
    name: z.string().min(2, 'Name must be at least 2 characters'),
    email: z.string().email('Enter a valid email'),
    password: z.string().min(6, 'Password must be at least 6 characters'),
    distributor_name: z.string().min(2, 'Business name is required'),
    country: z.string().optional(),
    language: z.string().optional(),
    herbalife_level: z.string().optional(),
});

type RegisterFormValues = z.infer<typeof registerSchema>;

export default function RegisterPage() {
    const router = useRouter();
    const { t, i18n } = useTranslation();
    const login = useAuthStore((s) => s.login);
    const setLanguage = useAuthStore((s) => s.setLanguage);
    const [isLoading, setIsLoading] = useState(false);
    const [mounted, setMounted] = useState(false);

    // Waitlist and registration limit states
    const [isLimitReached, setIsLimitReached] = useState(false);
    const [waitlistEmail, setWaitlistEmail] = useState('');
    const [waitlistName, setWaitlistName] = useState('');
    const [waitlistSubmitted, setWaitlistSubmitted] = useState(false);
    const [waitlistLoading, setWaitlistLoading] = useState(false);

    useEffect(() => {
        setMounted(true);
        
        // Check if beta registration limit has been reached
        const checkStatus = async () => {
            try {
                const { data } = await apiClient.get('/auth/registration-status');
                if (data && data.available === false) {
                    setIsLimitReached(true);
                }
            } catch (err) {
                console.error("Failed to fetch registration status", err);
            }
        };
        checkStatus();
    }, []);

    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<RegisterFormValues>({
        resolver: zodResolver(registerSchema),
        defaultValues: {
            language: 'es',
        },
    });

    const onSubmit = async (values: RegisterFormValues) => {
        setIsLoading(true);
        try {
            const { data } = await apiClient.post<AuthResponse>('/auth/register', values);
            const res = data.data;

            login(res.user, res.access_token, res.refresh_token);
            setLanguage(values.language || 'es');
            // Also sync i18n UI language with registration preference
            i18n.changeLanguage(values.language || 'es');
            localStorage.setItem('i18nextLng', values.language || 'es');
            toast.success(t('auth.accountCreated'));
            router.push('/dashboard');
        } catch (err: unknown) {
            const error = err as { response?: { data?: { error?: string } } };
            toast.error(error.response?.data?.error || t('auth.registrationFailed'));
        } finally {
            setIsLoading(false);
        }
    };

    const handleGoogleSuccess = async (credentialResponse: any) => {
        setIsLoading(true);
        try {
            const { data } = await apiClient.post<AuthResponse>('/auth/google', {
                credential: credentialResponse.credential,
            });
            const res = data.data;

            login(res.user, res.access_token, res.refresh_token);
            setLanguage('es'); 
            toast.success(t('auth.googleAuthSuccess'));

            if (res.user.role === 'super_admin') {
                router.push('/admin/dashboard');
            } else {
                router.push('/dashboard');
            }
        } catch (err: unknown) {
            const error = err as { response?: { data?: { error?: string } } };
            toast.error(error.response?.data?.error || t('auth.googleSignupFailed'));
        } finally {
            setIsLoading(false);
        }
    };

    if (isLimitReached) {
        return (
            <Card className="border-border/50 shadow-xl w-full max-w-md mx-auto bg-background/90 backdrop-blur-md">
                <CardHeader className="text-center pb-4 border-b border-border/10">
                    <div className="mx-auto h-12 w-12 rounded-full bg-amber-500/10 flex items-center justify-center mb-2">
                        <Sparkles className="h-6 w-6 text-amber-500 animate-pulse" />
                    </div>
                    <CardTitle className="text-2xl font-bold tracking-tight text-foreground">
                        Fase Beta - Cupos Agotados
                    </CardTitle>
                    <CardDescription className="text-sm mt-1 text-muted-foreground">
                        ¡Gracias por tu gran interés en EnpiAI! Hemos completado temporalmente los 300 cupos de registro disponibles para esta fase de prueba beta cerrada.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4 pt-6">
                    {waitlistSubmitted ? (
                        <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 p-5 rounded-xl text-center space-y-2 animate-in fade-in zoom-in-95 duration-300">
                            <p className="font-bold text-sm">¡Te has registrado con éxito!</p>
                            <p className="text-xs leading-relaxed">
                                Te enviaremos un correo electrónico de inmediato en cuanto habilitemos nuevos cupos de prueba gratuitos.
                            </p>
                        </div>
                    ) : (
                        <form onSubmit={async (e) => {
                            e.preventDefault();
                            if (!waitlistEmail) {
                                toast.warning('Por favor ingresa tu correo electrónico.');
                                return;
                            }
                            setWaitlistLoading(true);
                            try {
                                await apiClient.post('/auth/register-waitlist', {
                                    email: waitlistEmail,
                                    name: waitlistName
                                });
                                setWaitlistSubmitted(true);
                                toast.success('¡Registro de lista de espera exitoso!');
                            } catch (err) {
                                toast.error('Ocurrió un error al registrarte. Inténtalo de nuevo.');
                            } finally {
                                setWaitlistLoading(false);
                            }
                        }} className="space-y-4">
                            <p className="text-xs text-muted-foreground text-center">
                                Déjanos tus datos abajo para notificarte en cuanto abramos nuevas vacantes de prueba gratuita:
                            </p>
                            <div className="space-y-1.5">
                                <Label htmlFor="w_name">Tu Nombre</Label>
                                <Input
                                    id="w_name"
                                    type="text"
                                    placeholder="John Doe"
                                    value={waitlistName}
                                    onChange={(e) => setWaitlistName(e.target.value)}
                                    disabled={waitlistLoading}
                                    className="bg-white/5"
                                />
                            </div>
                            <div className="space-y-1.5">
                                <Label htmlFor="w_email">Correo Electrónico</Label>
                                <Input
                                    id="w_email"
                                    type="email"
                                    placeholder="you@example.com"
                                    value={waitlistEmail}
                                    onChange={(e) => setWaitlistEmail(e.target.value)}
                                    required
                                    disabled={waitlistLoading}
                                    className="bg-white/5"
                                />
                            </div>
                            <Button type="submit" className="w-full bg-primary hover:bg-primary/95 text-white" disabled={waitlistLoading}>
                                {waitlistLoading ? 'Registrando...' : 'Notificarme cuando haya cupos'}
                            </Button>
                        </form>
                    )}
                </CardContent>
                <CardFooter className="flex justify-center border-t border-border/10 pt-4 pb-6">
                    <p className="text-sm text-muted-foreground">
                        ¿Ya tienes una cuenta?{' '}
                        <Link href="/login" className="text-primary underline-offset-4 hover:underline font-semibold">
                            Inicia Sesión
                        </Link>
                    </p>
                </CardFooter>
            </Card>
        );
    }

    return (
        <Card className="border-border/50 shadow-xl">
            <CardHeader className="text-center">
                <CardTitle className="text-2xl font-bold tracking-tight">
                    {t('auth.createAccount')}
                </CardTitle>
                <CardDescription>
                    {t('auth.createAccountDescription')}
                </CardDescription>
            </CardHeader>
            <CardContent>
                <div className="mb-4 flex justify-center min-h-[40px]">
                    {mounted ? (
                        <GoogleLogin
                            onSuccess={handleGoogleSuccess}
                            onError={() => toast.error(t('auth.googleLoginFailed'))}
                            theme="outline"
                            width="100%"
                            text="signup_with"
                        />
                    ) : (
                        <div className="h-10 w-full animate-pulse bg-muted rounded-md" />
                    )}
                </div>
                <div className="relative mb-4">
                    <div className="absolute inset-0 flex items-center">
                        <span className="w-full border-t" />
                    </div>
                    <div className="relative flex justify-center text-xs uppercase">
                        <span className="bg-background px-2 text-muted-foreground">
                            {t('auth.orContinueWithEmail')}
                        </span>
                    </div>
                </div>
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <Label htmlFor="name">{t('auth.yourName')}</Label>
                            <Input
                                id="name"
                                placeholder="John Doe"
                                {...register('name')}
                                disabled={isLoading}
                            />
                            {errors.name && (
                                <p className="text-sm text-destructive">{errors.name.message}</p>
                            )}
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="distributor_name">{t('auth.businessName')}</Label>
                            <Input
                                id="distributor_name"
                                placeholder="My Wellness Co."
                                {...register('distributor_name')}
                                disabled={isLoading}
                            />
                            {errors.distributor_name && (
                                <p className="text-sm text-destructive">
                                    {errors.distributor_name.message}
                                </p>
                            )}
                        </div>
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="email">{t('common.email')}</Label>
                        <Input
                            id="email"
                            type="email"
                            placeholder="you@example.com"
                            {...register('email')}
                            disabled={isLoading}
                        />
                        {errors.email && (
                            <p className="text-sm text-destructive">{errors.email.message}</p>
                        )}
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="password">{t('common.password')}</Label>
                        <Input
                            id="password"
                            type="password"
                            placeholder="••••••"
                            {...register('password')}
                            disabled={isLoading}
                        />
                        {errors.password && (
                            <p className="text-sm text-destructive">
                                {errors.password.message}
                            </p>
                        )}
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="language">{t('auth.preferredLanguage')}</Label>
                        <select
                            id="language"
                            {...register('language')}
                            className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                            disabled={isLoading}
                        >
                            <option value="es">Español</option>
                            <option value="en">English</option>
                            <option value="pt">Português</option>
                        </select>
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="herbalife_level">Nivel de Distribuidor Inicial</Label>
                        <select
                            id="herbalife_level"
                            {...register('herbalife_level')}
                            className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                            disabled={isLoading}
                        >
                            <option value="Distribuidor Independiente">Distribuidor Independiente</option>
                            <option value="Consultor Mayor">Consultor Mayor</option>
                            <option value="Constructor del Éxito">Constructor del Éxito</option>
                            <option value="Productor Calificado">Productor Calificado</option>
                            <option value="Supervisor">Supervisor / Mayorista</option>
                            <option value="Equipo del Mundo">Equipo del Mundo</option>
                            <option value="Equipo del Mundo Activo">Equipo del Mundo Activo</option>
                            <option value="GET">Equipo de Expansión Global (GET)</option>
                            <option value="Equipo de Millonarios">Equipo de Millonarios</option>
                            <option value="Equipo del Presidente">Equipo del Presidente</option>
                            <option value="Club del Chairman">Club del Chairman</option>
                            <option value="Círculo del Fundador">Círculo del Fundador</option>
                        </select>
                    </div>
                    <Button type="submit" className="w-full" disabled={isLoading}>
                        {isLoading ? t('auth.creatingAccount') : t('auth.createAccount')}
                    </Button>
                </form>
            </CardContent>
            <CardFooter className="flex justify-center">
                <p className="text-sm text-muted-foreground">
                    {t('auth.alreadyHaveAccount')}{' '}
                    <Link href="/login" className="text-primary underline-offset-4 hover:underline">
                        {t('auth.signInLink')}
                    </Link>
                </p>
            </CardFooter>
        </Card>
    );
}
