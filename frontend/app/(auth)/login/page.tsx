'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'sonner';
import { GoogleLogin } from '@react-oauth/google';

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

const loginSchema = z.object({
    email: z.string().email('Enter a valid email'),
    password: z.string().min(6, 'Password must be at least 6 characters'),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export default function LoginPage() {
    const router = useRouter();
    const login = useAuthStore((s) => s.login);
    const [isLoading, setIsLoading] = useState(false);

    const {
        register,
        handleSubmit,
        formState: { errors },
    } = useForm<LoginFormValues>({
        resolver: zodResolver(loginSchema),
    });

    const onSubmit = async (values: LoginFormValues) => {
        setIsLoading(true);
        try {
            const { data } = await apiClient.post<AuthResponse>('/auth/login', values);
            const res = data.data;

            login(res.user, res.access_token, res.refresh_token);
            toast.success('Welcome back!');

            // Smart redirect based on role
            if (res.user.role === 'super_admin') {
                router.push('/admin/dashboard');
            } else {
                router.push('/dashboard');
            }
        } catch (err: unknown) {
            const error = err as { response?: { data?: { error?: string } } };
            toast.error(error.response?.data?.error || 'Login failed');
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
            toast.success('Welcome back!');

            // Smart redirect based on role
            if (res.user.role === 'super_admin') {
                router.push('/admin/dashboard');
            } else {
                router.push('/dashboard');
            }
        } catch (err: unknown) {
            const error = err as { response?: { data?: { error?: string } } };
            toast.error(error.response?.data?.error || 'Google login failed');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <Card className="border-border/50 shadow-xl">
            <CardHeader className="text-center">
                <CardTitle className="text-2xl font-bold tracking-tight">
                    Welcome Back
                </CardTitle>
                <CardDescription>Sign in to your EnpiAI account</CardDescription>
            </CardHeader>
            <CardContent>
                <div className="mb-4 flex justify-center">
                    <GoogleLogin
                        onSuccess={handleGoogleSuccess}
                        onError={() => toast.error('Google Sign-In failed')}
                        theme="outline"
                        width="100%"
                        text="continue_with"
                    />
                </div>
                <div className="relative mb-4">
                    <div className="absolute inset-0 flex items-center">
                        <span className="w-full border-t" />
                    </div>
                    <div className="relative flex justify-center text-xs uppercase">
                        <span className="bg-background px-2 text-muted-foreground">
                            Or continue with email
                        </span>
                    </div>
                </div>
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    <div className="space-y-2">
                        <Label htmlFor="email">Email</Label>
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
                        <Label htmlFor="password">Password</Label>
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
                    <Button type="submit" className="w-full" disabled={isLoading}>
                        {isLoading ? 'Signing in...' : 'Sign In'}
                    </Button>
                </form>
            </CardContent>
            <CardFooter className="flex justify-center">
                <p className="text-sm text-muted-foreground">
                    Don&apos;t have an account?{' '}
                    <Link href="/register" className="text-primary underline-offset-4 hover:underline">
                        Register
                    </Link>
                </p>
            </CardFooter>
        </Card>
    );
}
