'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Check, Loader2, CreditCard } from 'lucide-react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import apiClient from '@/lib/api-client';
import { useAuthStore } from '@/store/use-auth-store';

interface Plan {
    id: number;
    name: string;
    description: string;
    price_monthly: number;
    price_annual: number;
    currency: string;
    features: {
        max_agents: number;
        channels: string[];
        rag_enabled: boolean;
        analytics_enabled: boolean;
    };
    is_default: boolean;
}

export default function SubscribePage() {
    const router = useRouter();
    const login = useAuthStore((s) => s.login);
    const [isAnnual, setIsAnnual] = useState(false);
    const [selectedPlanId, setSelectedPlanId] = useState<number | null>(null);

    // Form State
    const [formData, setFormData] = useState({
        name: '',
        email: '',
        password: '',
        business_name: '',
        country: 'Ecuador',
    });

    // Fetch Plans
    const { data: plans, isLoading: plansLoading } = useQuery({
        queryKey: ['public-plans'],
        queryFn: async () => {
            const { data } = await apiClient.get<{ data: Plan[] }>('/payments/plans');
            return data.data;
        },
    });

    // Subscribe Mutation
    const subscribeMutation = useMutation({
        mutationFn: async () => {
            if (!selectedPlanId) throw new Error('Please select a plan');

            const { data } = await apiClient.post('/payments/subscribe', {
                ...formData,
                plan_id: selectedPlanId,
                interval: isAnnual ? 'annual' : 'monthly',
            });
            return data;
        },
        onSuccess: (data: any) => {
            // 1. Auto-login immediately so they have a session
            login(data.data.user, data.data.access_token, data.data.refresh_token);

            // 2. Redirect to Rebill Payment Link if available
            if (data.checkoutUrl) {
                toast.success('Redirecting to payment...');
                window.location.href = data.checkoutUrl;
            } else {
                // Determine fallback or if it was a free plan (not currently supported but good for safety)
                toast.success('Subscription active! Welcome to EnpiAI.');
                router.push('/dashboard');
            }
        },
        onError: (error: any) => {
            const message = error.response?.data?.error || 'Subscription failed';
            toast.error(message);
        },
    });

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData({ ...formData, [e.target.id]: e.target.value });
    };

    if (plansLoading) {
        return (
            <div className="flex h-screen items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    const sortedPlans = plans?.sort((a, b) => a.price_monthly - b.price_monthly) || [];

    return (
        <div className="min-h-screen bg-background py-10">
            <div className="container mx-auto max-w-5xl px-4">
                <div className="mb-10 text-center">
                    <h1 className="text-4xl font-extrabold tracking-tight lg:text-5xl">
                        Choose Your Plan
                    </h1>
                    <p className="mt-4 text-lg text-muted-foreground">
                        Unlock the power of AI for your Herbalife business.
                    </p>

                    <div className="mt-6 flex items-center justify-center gap-4">
                        <span className={!isAnnual ? 'font-bold' : 'text-muted-foreground'}>Monthly</span>
                        <Switch checked={isAnnual} onCheckedChange={setIsAnnual} />
                        <span className={isAnnual ? 'font-bold' : 'text-muted-foreground'}>
                            Annual <span className="text-xs text-green-600 font-bold">(Save 20%)</span>
                        </span>
                    </div>
                </div>

                <div className="grid gap-8 lg:grid-cols-2">
                    {/* Plan Selection */}
                    <div className="space-y-6">
                        {sortedPlans.map((plan) => (
                            <div
                                key={plan.id}
                                onClick={() => setSelectedPlanId(plan.id)}
                                className={`cursor-pointer rounded-xl border-2 p-6 transition-all ${selectedPlanId === plan.id
                                    ? 'border-primary bg-primary/5 shadow-lg'
                                    : 'border-border hover:border-primary/50'
                                    }`}
                            >
                                <div className="flex items-center justify-between">
                                    <div>
                                        <h3 className="text-xl font-bold">{plan.name}</h3>
                                        <p className="text-sm text-muted-foreground">{plan.description}</p>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-2xl font-bold">
                                            ${isAnnual ? plan.price_annual : plan.price_monthly}
                                        </div>
                                        <div className="text-xs text-muted-foreground">
                                            /{isAnnual ? 'year' : 'month'}
                                        </div>
                                    </div>
                                </div>
                                <ul className="mt-4 space-y-2 text-sm">
                                    <li className="flex items-center gap-2">
                                        <Check className="h-4 w-4 text-green-500" />
                                        {plan.features.max_agents} AI Agent{plan.features.max_agents > 1 && 's'}
                                    </li>
                                    <li className="flex items-center gap-2">
                                        <Check className="h-4 w-4 text-green-500" />
                                        {plan.features.channels.join(', ')} channels
                                    </li>
                                    {plan.features.rag_enabled && (
                                        <li className="flex items-center gap-2">
                                            <Check className="h-4 w-4 text-green-500" />
                                            Document Knowledge Base (RAG)
                                        </li>
                                    )}
                                </ul>
                            </div>
                        ))}
                    </div>

                    {/* Registration Form */}
                    <Card className="h-fit">
                        <CardHeader>
                            <CardTitle>Create Account</CardTitle>
                            <CardDescription>
                                Secure your subscription and start automating.
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="grid gap-2">
                                <Label htmlFor="name">Full Name</Label>
                                <Input
                                    id="name"
                                    placeholder="Jane Doe"
                                    value={formData.name}
                                    onChange={handleInputChange}
                                />
                            </div>
                            <div className="grid gap-2">
                                <Label htmlFor="email">Email</Label>
                                <Input
                                    id="email"
                                    type="email"
                                    placeholder="jane@example.com"
                                    value={formData.email}
                                    onChange={handleInputChange}
                                />
                            </div>
                            <div className="grid gap-2">
                                <Label htmlFor="password">Password</Label>
                                <Input
                                    id="password"
                                    type="password"
                                    value={formData.password}
                                    onChange={handleInputChange}
                                />
                            </div>
                            <div className="grid gap-2">
                                <Label htmlFor="business_name">Business Name (Optional)</Label>
                                <Input
                                    id="business_name"
                                    placeholder="Jane's Wellness Club"
                                    value={formData.business_name}
                                    onChange={handleInputChange}
                                />
                            </div>
                        </CardContent>
                        <CardFooter>
                            <Button
                                className="w-full"
                                size="lg"
                                onClick={() => subscribeMutation.mutate()}
                                disabled={subscribeMutation.isPending || !selectedPlanId || !formData.name || !formData.email || !formData.password}
                            >
                                {subscribeMutation.isPending ? (
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                ) : (
                                    <CreditCard className="mr-2 h-4 w-4" />
                                )}
                                {selectedPlanId
                                    ? `Pay & Subscribe`
                                    : 'Select a Plan to Continue'}
                            </Button>
                        </CardFooter>
                    </Card>
                </div>
            </div>
        </div>
    );
}
