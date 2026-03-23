'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Save, User, Building2, Globe, Key, Eye, EyeOff, Copy, Check } from 'lucide-react';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { toast } from 'sonner';
import apiClient from '@/lib/api-client';

interface DistributorSettings {
    id: number;
    name: string;
    herbalife_id: string | null;
    herbalife_level: string | null;
    business_name: string | null;
    country: string | null;
    city: string | null;
    timezone: string | null;
    language: string;
    email: string | null;
    phone: string | null;
    website: string | null;
    instagram: string | null;
    facebook: string | null;
    personal_story: string | null;
    api_key?: string | null;
    agent_name: string | null;
    llm_provider: string | null;
    llm_model: string | null;
}

import { useTranslation } from 'react-i18next';

export default function SettingsPage() {
    const { t } = useTranslation();
    const queryClient = useQueryClient();
    const [showApiKey, setShowApiKey] = useState(false);
    const [copied, setCopied] = useState(false);

    const { data: settings, isLoading } = useQuery({
        queryKey: ['distributor-settings'],
        queryFn: async () => {
            const { data } = await apiClient.get<{ data: DistributorSettings }>('/distributors/settings');
            return data.data;
        },
    });

    const [form, setForm] = useState<Partial<DistributorSettings>>({});

    // Populate form when data loads
    const formData = { ...settings, ...form };

    const updateMutation = useMutation({
        mutationFn: async (payload: Partial<DistributorSettings>) => {
            const { data } = await apiClient.put('/distributors/settings', payload);
            return data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['distributor-settings'] });
            toast.success(t('common.success', { defaultValue: 'Settings saved — your profile has been updated.' }));
            setForm({});
        },
        onError: (error: unknown) => {
            const message = (error as { response?: { data?: { error?: string } } })?.response?.data?.error || t('common.error', { defaultValue: 'Failed to save settings' });
            toast.error(message);
        },
    });

    const handleSave = () => {
        if (Object.keys(form).length === 0) {
            toast.info(t('common.noChanges', { defaultValue: 'No changes to save.' }));
            return;
        }
        updateMutation.mutate(form);
    };

    const handleChange = (field: keyof DistributorSettings, value: string) => {
        setForm((prev) => ({ ...prev, [field]: value }));
    };

    const copyApiKey = async () => {
        if (settings?.api_key) {
            await navigator.clipboard.writeText(settings.api_key);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    if (isLoading) {
        return (
            <div className="space-y-6">
                <Skeleton className="h-10 w-48" />
                <Skeleton className="h-64 w-full" />
                <Skeleton className="h-64 w-full" />
            </div>
        );
    }

    return (
        <div className="mx-auto max-w-4xl space-y-8">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">{t('settings.title')}</h2>
                    <p className="text-muted-foreground">
                        {t('settings.description')}
                    </p>
                </div>
                <Button onClick={handleSave} disabled={updateMutation.isPending}>
                    <Save className="mr-2 h-4 w-4" />
                    {updateMutation.isPending ? t('common.saving') : t('common.save')}
                </Button>
            </div>

            {/* Personal Information */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <User className="h-5 w-5" />
                        {t('settings.personalInfo')}
                    </CardTitle>
                    <CardDescription>{t('settings.personalInfoDesc')}</CardDescription>
                </CardHeader>
                <CardContent className="grid gap-6 md:grid-cols-2">
                    <div className="space-y-2">
                        <Label htmlFor="name">{t('common.name')}</Label>
                        <Input
                            id="name"
                            value={formData.name || ''}
                            onChange={(e) => handleChange('name', e.target.value)}
                            placeholder={t('common.name')}
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="email">{t('common.email')}</Label>
                        <Input
                            id="email"
                            type="email"
                            value={formData.email || ''}
                            onChange={(e) => handleChange('email', e.target.value)}
                            placeholder="you@example.com"
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="phone">{t('common.phone')}</Label>
                        <Input
                            id="phone"
                            value={formData.phone || ''}
                            onChange={(e) => handleChange('phone', e.target.value)}
                            placeholder="+1234567890"
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="personal_story">{t('settings.personalStory')}</Label>
                        <Input
                            id="personal_story"
                            value={formData.personal_story || ''}
                            onChange={(e) => handleChange('personal_story', e.target.value)}
                            placeholder={t('settings.personalStoryPlaceholder')}
                        />
                    </div>
                </CardContent>
            </Card>

            {/* Business Information */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Building2 className="h-5 w-5" />
                        {t('settings.businessInfo')}
                    </CardTitle>
                    <CardDescription>{t('settings.businessInfoDesc')}</CardDescription>
                </CardHeader>
                <CardContent className="grid gap-6 md:grid-cols-2">
                    <div className="space-y-2">
                        <Label htmlFor="business_name">{t('settings.businessName')}</Label>
                        <Input
                            id="business_name"
                            value={formData.business_name || ''}
                            onChange={(e) => handleChange('business_name', e.target.value)}
                            placeholder={t('settings.businessName')}
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="herbalife_id">Herbalife ID</Label>
                        <Input
                            id="herbalife_id"
                            value={formData.herbalife_id || ''}
                            onChange={(e) => handleChange('herbalife_id', e.target.value)}
                            placeholder="Your Herbalife member ID"
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="website">{t('settings.website')}</Label>
                        <Input
                            id="website"
                            value={formData.website || ''}
                            onChange={(e) => handleChange('website', e.target.value)}
                            placeholder="https://yoursite.com"
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="instagram">Instagram</Label>
                        <Input
                            id="instagram"
                            value={formData.instagram || ''}
                            onChange={(e) => handleChange('instagram', e.target.value)}
                            placeholder="@yourhandle"
                        />
                    </div>
                </CardContent>
            </Card>

            {/* Localization */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Globe className="h-5 w-5" />
                        {t('settings.localization')}
                    </CardTitle>
                    <CardDescription>{t('settings.localizationDesc')}</CardDescription>
                </CardHeader>
                <CardContent className="grid gap-6 md:grid-cols-3">
                    <div className="space-y-2">
                        <Label htmlFor="language">{t('settings.language')}</Label>
                        <select
                            id="language"
                            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                            value={formData.language || 'en'}
                            onChange={(e) => handleChange('language', e.target.value)}
                        >
                            <option value="en">{t('common.english')}</option>
                            <option value="es">{t('common.spanish')}</option>
                            <option value="pt">{t('common.portuguese')}</option>
                        </select>
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="country">{t('settings.country')}</Label>
                        <Input
                            id="country"
                            value={formData.country || ''}
                            onChange={(e) => handleChange('country', e.target.value)}
                            placeholder="Ecuador"
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="city">{t('settings.city')}</Label>
                        <Input
                            id="city"
                            value={formData.city || ''}
                            onChange={(e) => handleChange('city', e.target.value)}
                            placeholder="Quito"
                        />
                    </div>
                </CardContent>
            </Card>

            {/* API Key */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Key className="h-5 w-5" />
                        {t('settings.apiAccess')}
                    </CardTitle>
                    <CardDescription>
                        {t('settings.apiAccessDesc')}
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center gap-2">
                        <div className="relative flex-1">
                            <Input
                                readOnly
                                type={showApiKey ? 'text' : 'password'}
                                value={settings?.api_key || t('settings.noApiKey')}
                                className="pr-20 font-mono text-sm"
                            />
                        </div>
                        <Button
                            variant="outline"
                            size="icon"
                            onClick={() => setShowApiKey(!showApiKey)}
                            title={showApiKey ? t('common.hide') : t('common.show')}
                        >
                            {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </Button>
                        <Button
                            variant="outline"
                            size="icon"
                            onClick={copyApiKey}
                            title={t('common.copy')}
                            disabled={!settings?.api_key}
                        >
                            {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
                        </Button>
                    </div>
                    <Separator className="my-4" />
                    <div className="rounded-lg bg-muted/50 p-4">
                        <p className="text-sm text-muted-foreground">
                            <strong>{t('settings.endpoint')}:</strong>{' '}
                            <code className="rounded bg-muted px-1.5 py-0.5 text-xs">
                                {typeof window !== 'undefined' ? window.location.origin.replace(':3000', ':5000') : 'http://localhost:5000'}
                                /api/openai-compat/v1/chat/completions
                            </code>
                        </p>
                        <p className="mt-1 text-sm text-muted-foreground">
                            <strong>{t('settings.header')}:</strong>{' '}
                            <code className="rounded bg-muted px-1.5 py-0.5 text-xs">
                                Authorization: Bearer {'<your-api-key>'}
                            </code>
                        </p>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
