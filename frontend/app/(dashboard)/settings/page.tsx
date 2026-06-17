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
    whatsapp_phone: string | null;
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

const COUNTRY_PREFIXES = [
    // 4-digit prefixes (NANP Caribbean countries) first, so they match before +1
    { code: '+1242', label: '🇧🇸 Bahamas (+1242)' },
    { code: '+1246', label: '🇧🇧 Barbados (+1246)' },
    { code: '+1268', label: '🇦🇬 Antigua y Barbuda (+1268)' },
    { code: '+1473', label: '🇬🇩 Granada (+1473)' },
    { code: '+1758', label: '🇱🇨 Santa Lucía (+1758)' },
    { code: '+1767', label: '🇩🇲 Dominica (+1767)' },
    { code: '+1784', label: '🇻🇨 San Vicente y las Granadinas (+1784)' },
    { code: '+1809', label: '🇩🇴 Rep. Dominicana (+1809)' },
    { code: '+1829', label: '🇩🇴 Rep. Dominicana (+1829)' },
    { code: '+1849', label: '🇩🇴 Rep. Dominicana (+1849)' },
    { code: '+1868', label: '🇹🇹 Trinidad y Tobago (+1868)' },
    { code: '+1869', label: '🇰🇳 San Cristóbal y Nieves (+1869)' },
    { code: '+1876', label: '🇯🇲 Jamaica (+1876)' },
    
    // 3-digit prefixes
    { code: '+501', label: '🇧🇿 Belice (+501)' },
    { code: '+502', label: '🇬🇹 Guatemala (+502)' },
    { code: '+503', label: '🇸🇻 El Salvador (+503)' },
    { code: '+504', label: '🇭🇳 Honduras (+504)' },
    { code: '+505', label: '🇳🇮 Nicaragua (+505)' },
    { code: '+506', label: '🇨🇷 Costa Rica (+506)' },
    { code: '+507', label: '🇵🇦 Panamá (+507)' },
    { code: '+509', label: '🇭🇹 Haití (+509)' },
    { code: '+591', label: '🇧🇴 Bolivia (+591)' },
    { code: '+592', label: '🇬🇾 Guyana (+592)' },
    { code: '+593', label: '🇪🇨 Ecuador (+593)' },
    { code: '+595', label: '🇵🇾 Paraguay (+595)' },
    { code: '+597', label: '🇸🇷 Surinam (+597)' },
    { code: '+598', label: '🇺🇾 Uruguay (+598)' },
    
    // 2-digit prefixes
    { code: '+51', label: '🇵🇪 Perú (+51)' },
    { code: '+52', label: '🇲🇽 México (+52)' },
    { code: '+53', label: '🇨🇺 Cuba (+53)' },
    { code: '+54', label: '🇦🇷 Argentina (+54)' },
    { code: '+55', label: '🇧🇷 Brasil (+55)' },
    { code: '+56', label: '🇨🇱 Chile (+56)' },
    { code: '+57', label: '🇨🇴 Colombia (+57)' },
    { code: '+58', label: '🇻🇪 Venezuela (+58)' },
    { code: '+34', label: '🇪🇸 España (+34)' },
    
    // 1-digit prefixes last, so they don't overshadow 4-digit prefixes starting with +1
    { code: '+1', label: '🇺🇸 Estados Unidos (+1)' },
    { code: '+1', label: '🇨🇦 Canadá (+1)' },
];

const AMERICAN_COUNTRIES = [
    "Canadá", "Estados Unidos", "México",
    "Antigua y Barbuda", "Bahamas", "Barbados", "Belice", "Costa Rica", "Cuba", "Dominica",
    "El Salvador", "Granada", "Guatemala", "Haití", "Honduras", "Jamaica", "Nicaragua",
    "Panamá", "República Dominicana", "San Cristóbal y Nieves", "San Vicente y las Granadinas",
    "Santa Lucía", "Trinidad y Tobago",
    "Argentina", "Bolivia", "Brasil", "Chile", "Colombia", "Ecuador", "Guyana",
    "Paraguay", "Perú", "Surinam", "Uruguay", "Venezuela"
];

function parsePhoneNumber(value: string) {
    const prefixObj = COUNTRY_PREFIXES.find(p => value.startsWith(p.code));
    if (prefixObj) {
        let local = value.slice(prefixObj.code.length);
        // Strip legacy leading zeros
        local = local.replace(/^0+/, '');
        return {
            prefix: prefixObj.code,
            localNumber: local,
        };
    }
    return {
        prefix: '+593',
        localNumber: value || '',
    };
}

const getLevelTranslationKey = (lvl: string) => {
    switch (lvl) {
        case 'Distribuidor Independiente': return 'levels.distribuidor';
        case 'Consultor Mayor': return 'levels.consultor';
        case 'Constructor del Éxito': return 'levels.constructor';
        case 'Productor Calificado': return 'levels.productor';
        case 'Supervisor': return 'levels.supervisor';
        case 'Equipo del Mundo': return 'levels.mundo';
        case 'Equipo del Mundo Activo': return 'levels.mundo_activo';
        case 'GET': return 'levels.get';
        case 'Equipo de Millonarios': return 'levels.millonarios';
        case 'Equipo del Presidente': return 'levels.presidente';
        case 'Club del Chairman': return 'levels.chairman';
        case 'Círculo del Fundador': return 'levels.fundador';
        default: return '';
    }
};

interface PhoneInputWithPrefixProps {
    id: string;
    label: string;
    value: string;
    onChange: (val: string) => void;
    helpText?: string;
    placeholder?: string;
}

function PhoneInputWithPrefix({ id, label, value, onChange, helpText, placeholder }: PhoneInputWithPrefixProps) {
    const { prefix, localNumber } = parsePhoneNumber(value || '');

    const handlePrefixChange = (newPrefix: string) => {
        onChange(newPrefix + localNumber);
    };

    const handleLocalNumberChange = (newLocal: string) => {
        let cleaned = newLocal.replace(/\D/g, '');
        // Strip duplicate pasted country code if matching selected prefix
        const cleanedPrefix = prefix.replace(/\D/g, '');
        if (cleaned.startsWith(cleanedPrefix)) {
            cleaned = cleaned.slice(cleanedPrefix.length);
        }
        // Strip any leading zeros
        cleaned = cleaned.replace(/^0+/, '');
        onChange(prefix + cleaned);
    };

    return (
        <div className="space-y-2">
            <Label htmlFor={id}>{label}</Label>
            <div className="flex gap-2">
                <select
                    value={prefix}
                    onChange={(e) => handlePrefixChange(e.target.value)}
                    className="flex h-10 w-[150px] rounded-md border border-input bg-background px-3 py-2 text-xs ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                    {COUNTRY_PREFIXES.map((p) => (
                        <option key={p.code} value={p.code}>
                            {p.label}
                        </option>
                    ))}
                </select>
                <Input
                    id={id}
                    type="tel"
                    value={localNumber}
                    onChange={(e) => handleLocalNumberChange(e.target.value)}
                    placeholder={placeholder || "0991234567"}
                    className="flex-1"
                />
            </div>
            {helpText && (
                <p className="text-[10px] text-muted-foreground">
                    {helpText}
                </p>
            )}
        </div>
    );
}

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
                            <PhoneInputWithPrefix
                                id="phone"
                                label={t('common.phone')}
                                value={formData.phone || ''}
                                onChange={(val) => handleChange('phone', val)}
                                placeholder="0991234567"
                            />
                            <PhoneInputWithPrefix
                                id="whatsapp_phone"
                                label={t('settings.whatsappPhone')}
                                value={formData.whatsapp_phone || ''}
                                onChange={(val) => handleChange('whatsapp_phone', val)}
                                placeholder="0991234567"
                                helpText={t('settings.whatsappPhoneHelp')}
                            />
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
                                <Label htmlFor="herbalife_level">{t('settings.distributorLevel')}</Label>
                                <select
                                    id="herbalife_level"
                                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                                    value={formData.herbalife_level || 'Distribuidor Independiente'}
                                    onChange={(e) => handleChange('herbalife_level', e.target.value)}
                                >
                                    <option value="Distribuidor Independiente">{t('levels.distribuidor')}</option>
                                    <option value="Consultor Mayor">{t('levels.consultor')}</option>
                                    <option value="Constructor del Éxito">{t('levels.constructor')}</option>
                                    <option value="Productor Calificado">{t('levels.productor')}</option>
                                    <option value="Supervisor">{t('levels.supervisor')}</option>
                                    <option value="Equipo del Mundo">{t('levels.mundo')}</option>
                                    <option value="Equipo del Mundo Activo">{t('levels.mundo_activo')}</option>
                                    <option value="GET">{t('levels.get')}</option>
                                    <option value="Equipo de Millonarios">{t('levels.millonarios')}</option>
                                    <option value="Equipo del Presidente">{t('levels.presidente')}</option>
                                    <option value="Club del Chairman">{t('levels.chairman')}</option>
                                    <option value="Círculo del Fundador">{t('levels.fundador')}</option>
                                </select>
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
                                <select
                                    id="country"
                                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                                    value={formData.country || ''}
                                    onChange={(e) => handleChange('country', e.target.value)}
                                >
                                    <option value="" disabled>{t('settings.selectCountry') || 'Seleccionar país'}</option>
                                    {formData.country && !AMERICAN_COUNTRIES.includes(formData.country) && (
                                        <option value={formData.country}>{formData.country}</option>
                                    )}
                                    <optgroup label="América del Norte">
                                        <option value="Canadá">Canadá</option>
                                        <option value="Estados Unidos">Estados Unidos</option>
                                        <option value="México">México</option>
                                    </optgroup>
                                    <optgroup label="América Central y las Antillas">
                                        <option value="Antigua y Barbuda">Antigua y Barbuda</option>
                                        <option value="Bahamas">Bahamas</option>
                                        <option value="Barbados">Barbados</option>
                                        <option value="Belice">Belice</option>
                                        <option value="Costa Rica">Costa Rica</option>
                                        <option value="Cuba">Cuba</option>
                                        <option value="Dominica">Dominica</option>
                                        <option value="El Salvador">El Salvador</option>
                                        <option value="Granada">Granada</option>
                                        <option value="Guatemala">Guatemala</option>
                                        <option value="Haití">Haití</option>
                                        <option value="Honduras">Honduras</option>
                                        <option value="Jamaica">Jamaica</option>
                                        <option value="Nicaragua">Nicaragua</option>
                                        <option value="Panamá">Panamá</option>
                                        <option value="República Dominicana">República Dominicana</option>
                                        <option value="San Cristóbal y Nieves">San Cristóbal y Nieves</option>
                                        <option value="San Vicente y las Granadinas">San Vicente y las Granadinas</option>
                                        <option value="Santa Lucía">Santa Lucía</option>
                                        <option value="Trinidad y Tobago">Trinidad y Tobago</option>
                                    </optgroup>
                                    <optgroup label="América del Sur">
                                        <option value="Argentina">Argentina</option>
                                        <option value="Bolivia">Bolivia</option>
                                        <option value="Brasil">Brasil</option>
                                        <option value="Chile">Chile</option>
                                        <option value="Colombia">Colombia</option>
                                        <option value="Ecuador">Ecuador</option>
                                        <option value="Guyana">Guyana</option>
                                        <option value="Paraguay">Paraguay</option>
                                        <option value="Perú">Perú</option>
                                        <option value="Surinam">Surinam</option>
                                        <option value="Uruguay">Uruguay</option>
                                        <option value="Venezuela">Venezuela</option>
                                    </optgroup>
                                </select>
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
