'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'sonner';
import { GoogleLogin } from '@react-oauth/google';
import { useTranslation } from 'react-i18next';

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
});

type RegisterFormValues = z.infer<typeof registerSchema>;

export default function RegisterPage() {
    const router = useRouter();
    const { t, i18n } = useTranslation();
    const login = useAuthStore((s) => s.login);
    const setLanguage = useAuthStore((s) => s.setLanguage);
    const [isLoading, setIsLoading] = useState(false);

    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<RegisterFormValues>({
        resolver: zodResolver(registerSchema),
        defaultValues: {
            language: 'en',
        },
    });

    const onSubmit = async (values: RegisterFormValues) => {
        setIsLoading(true);
        try {
            const { data } = await apiClient.post<AuthResponse>('/auth/register', values);
            const res = data.data;

            login(res.user, res.access_token, res.refresh_token);
            setLanguage(values.language || 'en');
            // Also sync i18n UI language with registration preference
            i18n.changeLanguage(values.language || 'en');
            localStorage.setItem('i18nextLng', values.language || 'en');
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
            setLanguage('en'); 
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
                <div className="mb-4 flex justify-center">
                    <GoogleLogin
                        onSuccess={handleGoogleSuccess}
                        onError={() => toast.error(t('auth.googleLoginFailed'))}
                        theme="outline"
                        width="100%"
                        text="signup_with"
                    />
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
                            <option value="en">English</option>
                            <option value="es">Español</option>
                            <option value="pt">Português</option>
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
