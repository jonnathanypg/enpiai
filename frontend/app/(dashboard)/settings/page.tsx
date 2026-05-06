'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Save, User, Building2, Globe, Lock, Eye, EyeOff } from 'lucide-react';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

import { Skeleton } from '@/components/ui/skeleton';
import { toast } from 'sonner';
import apiClient from '@/lib/api-client';
import { useAuthStore } from '@/store/use-auth-store';

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
    const user = useAuthStore((s) => s.user);
    const isSuperAdmin = user?.role === 'super_admin';

    const { data: settings, isLoading } = useQuery({
        queryKey: ['distributor-settings'],
        queryFn: async () => {
            const { data } = await apiClient.get<{ data: DistributorSettings }>('/distributors/settings');
            return data.data;
        },
        enabled: !isSuperAdmin, // Only fetch for distributors
    });

    const updateUser = useAuthStore(state => state.updateUser);

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
            
            // Sync specific globally-needed fields like herbalife_id
            if (form.herbalife_id !== undefined || form.name !== undefined) {
                updateUser({
                    herbalife_id: form.herbalife_id,
                    name: form.name
                } as any);
            }
            
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

    // --- Password Change State ---
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [showCurrentPassword, setShowCurrentPassword] = useState(false);
    const [showNewPassword, setShowNewPassword] = useState(false);

    const changePasswordMutation = useMutation({
        mutationFn: async (payload: { current_password: string; new_password: string }) => {
            const { data } = await apiClient.post('/auth/change-password', payload);
            return data;
        },
        onSuccess: () => {
            toast.success(t('settings.passwordChanged', { defaultValue: 'Password updated successfully.' }));
            setCurrentPassword('');
            setNewPassword('');
            setConfirmPassword('');
        },
        onError: (error: unknown) => {
            const message = (error as { response?: { data?: { error?: string } } })?.response?.data?.error || t('common.error', { defaultValue: 'Failed to change password' });
            toast.error(message);
        },
    });

    const handleChangePassword = () => {
        if (!currentPassword || !newPassword) {
            toast.error(t('settings.fillAllFields', { defaultValue: 'Please fill in all password fields.' }));
            return;
        }
        if (newPassword.length < 6) {
            toast.error(t('settings.passwordMinLength', { defaultValue: 'New password must be at least 6 characters.' }));
            return;
        }
        if (newPassword !== confirmPassword) {
            toast.error(t('settings.passwordsDoNotMatch', { defaultValue: 'New passwords do not match.' }));
            return;
        }
        changePasswordMutation.mutate({
            current_password: currentPassword,
            new_password: newPassword,
        });
    };

    if (isLoading && !isSuperAdmin) {
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
                        {isSuperAdmin
                            ? t('settings.descriptionAdmin', { defaultValue: 'Manage your account security.' })
                            : t('settings.description')}
                    </p>
                </div>
                {!isSuperAdmin && (
                    <Button onClick={handleSave} disabled={updateMutation.isPending}>
                        <Save className="mr-2 h-4 w-4" />
                        {updateMutation.isPending ? t('common.saving') : t('common.save')}
                    </Button>
                )}
            </div>

            {/* ===== Distributor-only sections ===== */}
            {!isSuperAdmin && (
                <>
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
                </>
            )}

            {/* ===== Security (Password Change) — Available to ALL roles ===== */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Lock className="h-5 w-5" />
                        {t('settings.security', { defaultValue: 'Security' })}
                    </CardTitle>
                    <CardDescription>{t('settings.securityDesc', { defaultValue: 'Update your account password.' })}</CardDescription>
                </CardHeader>
                <CardContent className="grid gap-6 md:grid-cols-2">
                    <div className="space-y-2">
                        <Label htmlFor="current_password">{t('settings.currentPassword', { defaultValue: 'Current Password' })}</Label>
                        <div className="relative">
                            <Input
                                id="current_password"
                                type={showCurrentPassword ? 'text' : 'password'}
                                value={currentPassword}
                                onChange={(e) => setCurrentPassword(e.target.value)}
                                placeholder="••••••••"
                            />
                            <button
                                type="button"
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                                onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                            >
                                {showCurrentPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                            </button>
                        </div>
                    </div>
                    <div /> {/* Spacer for grid alignment */}
                    <div className="space-y-2">
                        <Label htmlFor="new_password">{t('settings.newPassword', { defaultValue: 'New Password' })}</Label>
                        <div className="relative">
                            <Input
                                id="new_password"
                                type={showNewPassword ? 'text' : 'password'}
                                value={newPassword}
                                onChange={(e) => setNewPassword(e.target.value)}
                                placeholder="••••••••"
                            />
                            <button
                                type="button"
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                                onClick={() => setShowNewPassword(!showNewPassword)}
                            >
                                {showNewPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                            </button>
                        </div>
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="confirm_password">{t('settings.confirmPassword', { defaultValue: 'Confirm New Password' })}</Label>
                        <Input
                            id="confirm_password"
                            type="password"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            placeholder="••••••••"
                        />
                    </div>
                    <div className="md:col-span-2 flex justify-end">
                        <Button
                            onClick={handleChangePassword}
                            disabled={changePasswordMutation.isPending}
                            variant="outline"
                        >
                            <Lock className="mr-2 h-4 w-4" />
                            {changePasswordMutation.isPending
                                ? t('common.saving')
                                : t('settings.updatePassword', { defaultValue: 'Update Password' })}
                        </Button>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
