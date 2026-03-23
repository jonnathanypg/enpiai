'use client';

import { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
    Radio,
    Smartphone,
    MessageCircle,
    Mail,
    CheckCircle2,
    AlertCircle,
    Loader2,
    Save,
    ExternalLink,
    QrCode,
    Unplug,
    RefreshCw,
    XCircle,
} from 'lucide-react';
import { toast } from 'sonner';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import apiClient from '@/lib/api-client';
import { channelsService } from '@/services/channels-service';
import type { Channel } from '@/types';

// ─── Helpers ───────────────────────────────────────────────────────
import { useTranslation } from 'react-i18next';

function StatusBadge({ status }: { status: string }) {
    const { t } = useTranslation();
    if (status === 'active' || status === 'connected') {
        return (
            <Badge variant="outline" className="border-green-500 text-green-600">
                <CheckCircle2 className="mr-1 h-3 w-3" /> {t('channels.connected')}
            </Badge>
        );
    }
    return (
        <Badge variant="outline" className="border-yellow-500 text-yellow-600">
            <AlertCircle className="mr-1 h-3 w-3" /> {t('channels.notConnected')}
        </Badge>
    );
}

export default function ChannelsPage() {
    const { t } = useTranslation();
    const queryClient = useQueryClient();

    const { data: channels, isLoading } = useQuery({
        queryKey: ['channels'],
        queryFn: async () => {
            const { data } = await apiClient.get<{ data: Channel[] }>('/channels');
            return data.data;
        },
    });

    const whatsappChannel = channels?.find((c) => c.channel_type === 'whatsapp');
    const telegramChannel = channels?.find((c) => c.channel_type === 'telegram');
    const emailChannel = channels?.find((c) => c.channel_type === 'email');

    const saveMutation = useMutation({
        mutationFn: async (payload: {
            id?: number;
            channel_type: string;
            name: string;
            credentials: Record<string, string>;
        }) => {
            if (payload.id) {
                const { data } = await apiClient.put(`/channels/${payload.id}`, {
                    credentials: payload.credentials,
                    status: 'active',
                });
                return data;
            }
            const { data } = await apiClient.post('/channels', {
                channel_type: payload.channel_type,
                name: payload.name,
                credentials: payload.credentials,
                config: {},
            });
            return data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['channels'] });
            toast.success(t('common.save') + ' ' + t('common.success', { defaultValue: 'Success' }));
        },
        onError: (error: unknown) => {
            const message =
                (error as { response?: { data?: { error?: string } } })?.response?.data?.error ||
                t('common.error', { defaultValue: 'Failed to save channel' });
            toast.error(message);
        },
    });

    if (isLoading) {
        return (
            <div className="mx-auto max-w-3xl space-y-6">
                <Skeleton className="h-10 w-48" />
                <Skeleton className="h-48 w-full" />
                <Skeleton className="h-48 w-full" />
                <Skeleton className="h-48 w-full" />
            </div>
        );
    }

    return (
        <div className="mx-auto max-w-3xl space-y-8">
            <div>
                <h2 className="flex items-center gap-2 text-3xl font-bold tracking-tight">
                    <Radio className="h-7 w-7 text-primary" />
                    {t('channels.title')}
                </h2>
                <p className="text-muted-foreground">
                    {t('channels.description')}
                </p>
            </div>

            <WhatsAppCard channel={whatsappChannel} />

            <TelegramCard
                channel={telegramChannel}
                onSave={(token) =>
                    saveMutation.mutate({
                        id: telegramChannel?.id,
                        channel_type: 'telegram',
                        name: 'Telegram Bot',
                        credentials: { bot_token: token },
                    })
                }
                isSaving={saveMutation.isPending}
            />

            <EmailCard
                channel={emailChannel}
                onSave={(creds) =>
                    saveMutation.mutate({
                        id: emailChannel?.id,
                        channel_type: 'email',
                        name: 'Email SMTP',
                        credentials: creds,
                    })
                }
                isSaving={saveMutation.isPending}
            />

            <GoogleCard />
        </div>
    );
}

function WhatsAppCard({ channel }: { channel?: Channel }) {
    const { t } = useTranslation();
    const [isConnecting, setIsConnecting] = useState(false);
    const [qrCode, setQrCode] = useState<string | null>(null);
    const [isPolling, setIsPolling] = useState(false);
    const [isConnected, setIsConnected] = useState(false);
    const [connectedPhone, setConnectedPhone] = useState<string | null>(null);
    const [isDisconnecting, setIsDisconnecting] = useState(false);

    useEffect(() => {
        const checkStatus = async () => {
            try {
                const result = await channelsService.getWhatsAppStatus();
                setIsConnected(result.connected);
                if (result.phone) setConnectedPhone(result.phone);
            } catch (error) {
                console.error('Failed to check WhatsApp status:', error);
            }
        };
        checkStatus();
    }, []);

    useEffect(() => {
        if (!isPolling || !qrCode) return;

        const interval = setInterval(async () => {
            try {
                const result = await channelsService.getWhatsAppStatus();
                if (result.connected) {
                    setQrCode(null);
                    setIsPolling(false);
                    setIsConnected(true);
                    if (result.phone) setConnectedPhone(result.phone);
                    toast.success(t('common.success', { defaultValue: 'Success' }));
                } else {
                    try {
                        const qrResult = await channelsService.getWhatsAppQR();
                        if (qrResult.qr) {
                            setQrCode(qrResult.qr);
                        }
                    } catch {
                        // ignore
                    }
                }
            } catch (error) {
                console.error('WhatsApp status poll error:', error);
            }
        }, 3000);

        return () => clearInterval(interval);
    }, [isPolling, qrCode, t]);

    const handleConnect = async () => {
        setIsConnecting(true);
        try {
            await channelsService.initWhatsApp();

            setTimeout(async () => {
                try {
                    const qrResult = await channelsService.getWhatsAppQR();
                    if (qrResult.qr) {
                        setQrCode(qrResult.qr);
                        setIsPolling(true);
                    }
                } catch (error) {
                    console.error('Failed to get QR:', error);
                    toast.error(t('common.error', { defaultValue: 'Error' }));
                }
                setIsConnecting(false);
            }, 2500);
        } catch (error) {
            console.error('Failed to init WhatsApp:', error);
            toast.error(t('common.error', { defaultValue: 'Error' }));
            setIsConnecting(false);
        }
    };

    const handleDisconnect = async () => {
        setIsDisconnecting(true);
        try {
            await channelsService.disconnectWhatsApp();
            setQrCode(null);
            setIsPolling(false);
            setIsConnected(false);
            setConnectedPhone(null);
            toast.success(t('common.success', { defaultValue: 'Disconnected' }));
        } catch (error) {
            console.error('Failed to disconnect WhatsApp:', error);
            toast.error(t('common.error', { defaultValue: 'Error' }));
        } finally {
            setIsDisconnecting(false);
        }
    };

    const handleCancel = () => {
        setQrCode(null);
        setIsPolling(false);
        setIsConnecting(false);
    };

    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
                <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/30">
                        <Smartphone className="h-5 w-5 text-green-600" />
                    </div>
                    <div>
                        <CardTitle className="text-base">{t('channels.whatsappTitle')}</CardTitle>
                        <CardDescription>{t('channels.whatsappDesc')}</CardDescription>
                    </div>
                </div>
                <StatusBadge status={isConnected ? 'connected' : 'inactive'} />
            </CardHeader>
            <CardContent>
                {isConnected ? (
                    <div className="space-y-4">
                        <Alert className="bg-green-500/10 border-green-500/20">
                            <CheckCircle2 className="h-4 w-4 text-green-600" />
                            <AlertDescription className="text-green-700 dark:text-green-400">
                                {t('channels.connected')}{' '}
                                {connectedPhone && (
                                    <strong>{connectedPhone}</strong>
                                )}
                            </AlertDescription>
                        </Alert>
                        <Button
                            variant="destructive"
                            onClick={handleDisconnect}
                            disabled={isDisconnecting}
                            className="w-full"
                        >
                            {isDisconnecting ? (
                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            ) : (
                                <Unplug className="h-4 w-4 mr-2" />
                            )}
                            {isDisconnecting ? t('common.saving', { defaultValue: 'Disconnecting...' }) : t('common.delete', { defaultValue: 'Disconnect WhatsApp' })}
                        </Button>
                    </div>
                ) : qrCode ? (
                    <div className="space-y-4">
                        <div className="text-center">
                            <p className="text-sm text-muted-foreground mb-4">
                                {t('channels.whatsappDesc')}
                            </p>
                            <div className="bg-white p-4 rounded-lg inline-block shadow-sm border">
                                <img
                                    src={
                                        qrCode.startsWith('<svg')
                                            ? `data:image/svg+xml;base64,${typeof window !== 'undefined' ? window.btoa(qrCode) : ''}`
                                            : qrCode
                                    }
                                    alt="WhatsApp QR Code"
                                    className="w-56 h-56"
                                />
                            </div>
                            <p className="text-xs text-muted-foreground mt-4 flex items-center justify-center gap-1">
                                <RefreshCw className="h-3 w-3 animate-spin" />
                                {t('common.saving', { defaultValue: 'Waiting for connection...' })}
                            </p>
                        </div>
                        <Button
                            variant="outline"
                            onClick={handleCancel}
                            className="w-full"
                        >
                            {t('common.cancel', { defaultValue: 'Cancel' })}
                        </Button>
                    </div>
                ) : (
                    <div className="space-y-4">
                        <Alert>
                            <XCircle className="h-4 w-4" />
                            <AlertDescription>
                                {t('channels.whatsappNotConnected')}
                            </AlertDescription>
                        </Alert>
                        <Button
                            onClick={handleConnect}
                            disabled={isConnecting}
                            className="w-full bg-green-600 hover:bg-green-700 text-white"
                        >
                            {isConnecting ? (
                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            ) : (
                                <QrCode className="h-4 w-4 mr-2" />
                            )}
                            {isConnecting ? t('common.saving', { defaultValue: 'Generating QR...' }) : t('channels.connectWhatsapp')}
                        </Button>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

function TelegramCard({
    channel,
    onSave,
    isSaving,
}: {
    channel?: Channel;
    onSave: (token: string) => void;
    isSaving: boolean;
}) {
    const { t } = useTranslation();
    const [token, setToken] = useState('');

    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
                <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/30">
                        <MessageCircle className="h-5 w-5 text-blue-600" />
                    </div>
                    <div>
                        <CardTitle className="text-base">{t('channels.telegramTitle')}</CardTitle>
                        <CardDescription>{t('channels.telegramDesc')}</CardDescription>
                    </div>
                </div>
                <StatusBadge status={channel?.status || 'inactive'} />
            </CardHeader>
            <CardContent className="space-y-4">
                <div className="space-y-2">
                    <Label htmlFor="telegram_token">{t('common.token', { defaultValue: 'Bot Token' })}</Label>
                    <Input
                        id="telegram_token"
                        type="password"
                        placeholder={t('channels.telegramTokenPlaceholder')}
                        value={token}
                        onChange={(e) => setToken(e.target.value)}
                    />
                    <p className="text-xs text-muted-foreground">
                        {t('channels.getTokenHelp')}{' '}
                        <a
                            href="https://t.me/BotFather"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary underline"
                        >
                            @BotFather
                            <ExternalLink className="ml-0.5 inline h-3 w-3" />
                        </a>
                    </p>
                </div>
                <Button
                    onClick={() => onSave(token)}
                    disabled={!token.trim() || isSaving}
                    className="w-full"
                >
                    {isSaving ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                        <Save className="mr-2 h-4 w-4" />
                    )}
                    {channel ? t('common.save') : t('channels.connectTelegram')}
                </Button>
            </CardContent>
        </Card>
    );
}

function EmailCard({
    channel,
    onSave,
    isSaving,
}: {
    channel?: Channel;
    onSave: (creds: Record<string, string>) => void;
    isSaving: boolean;
}) {
    const { t } = useTranslation();
    const [host, setHost] = useState('');
    const [port, setPort] = useState('587');
    const [user, setUser] = useState('');
    const [pass, setPass] = useState('');

    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
                <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-orange-100 dark:bg-orange-900/30">
                        <Mail className="h-5 w-5 text-orange-600" />
                    </div>
                    <div>
                        <CardTitle className="text-base">{t('channels.emailTitle')}</CardTitle>
                        <CardDescription>{t('channels.emailDesc')}</CardDescription>
                    </div>
                </div>
                <StatusBadge status={channel?.status || 'inactive'} />
            </CardHeader>
            <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                        <Label htmlFor="smtp_host">{t('common.host', { defaultValue: 'SMTP Host' })}</Label>
                        <Input
                            id="smtp_host"
                            placeholder="smtp.gmail.com"
                            value={host}
                            onChange={(e) => setHost(e.target.value)}
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="smtp_port">{t('common.port', { defaultValue: 'Port' })}</Label>
                        <Input
                            id="smtp_port"
                            placeholder="587"
                            value={port}
                            onChange={(e) => setPort(e.target.value)}
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="smtp_user">{t('common.user', { defaultValue: 'Email / Username' })}</Label>
                        <Input
                            id="smtp_user"
                            placeholder="you@gmail.com"
                            value={user}
                            onChange={(e) => setUser(e.target.value)}
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="smtp_pass">{t('common.password')}</Label>
                        <Input
                            id="smtp_pass"
                            type="password"
                            placeholder="••••••••"
                            value={pass}
                            onChange={(e) => setPass(e.target.value)}
                        />
                    </div>
                </div>
                <Button
                    onClick={() =>
                        onSave({
                            smtp_host: host,
                            smtp_port: port,
                            smtp_user: user,
                            smtp_password: pass,
                        })
                    }
                    disabled={!host.trim() || !user.trim() || !pass.trim() || isSaving}
                    className="w-full"
                >
                    {isSaving ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                        <Save className="mr-2 h-4 w-4" />
                    )}
                    {channel ? t('common.save') : t('channels.connectEmail')}
                </Button>
            </CardContent>
        </Card>
    );
}

function GoogleCard() {
    const { t } = useTranslation();
    const { data: settings } = useQuery({
        queryKey: ['distributor-settings'],
        queryFn: async () => {
            const { data } = await apiClient.get<{ data: { google_credentials?: unknown } }>(
                '/distributors/settings'
            );
            return data.data;
        },
    });

    const isConnected = !!settings?.google_credentials;

    const handleGoogleLogin = async () => {
        try {
            const { data } = await apiClient.get<{ data: { authorization_url: string } }>(
                '/auth/google/login'
            );
            window.location.href = data.data.authorization_url;
        } catch {
            toast.error(t('common.error', { defaultValue: 'Error' }));
        }
    };

    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
                <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/30">
                        <svg className="h-5 w-5" viewBox="0 0 24 24">
                            <path
                                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
                                fill="#4285F4"
                            />
                            <path
                                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                                fill="#34A853"
                            />
                            <path
                                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                                fill="#FBBC05"
                            />
                            <path
                                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                                fill="#EA4335"
                            />
                        </svg>
                    </div>
                    <div>
                        <CardTitle className="text-base">{t('channels.googleTitle')}</CardTitle>
                        <CardDescription>{t('channels.googleDesc')}</CardDescription>
                    </div>
                </div>
                <StatusBadge status={isConnected ? 'active' : 'inactive'} />
            </CardHeader>
            <CardContent>
                {isConnected ? (
                    <p className="text-sm text-green-600">
                        ✓ {t('channels.connected')}
                    </p>
                ) : (
                    <>
                        <p className="mb-4 text-sm text-muted-foreground">
                            {t('channels.googleIntegrationDesc')}
                        </p>
                        <Button onClick={handleGoogleLogin} variant="outline" className="w-full">
                            <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24">
                                <path
                                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
                                    fill="#4285F4"
                                />
                                <path
                                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                                    fill="#34A853"
                                />
                                <path
                                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                                    fill="#FBBC05"
                                />
                                <path
                                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                                    fill="#EA4335"
                                />
                            </svg>
                            {t('channels.signInWithGoogle')}
                        </Button>
                    </>
                )}
            </CardContent>
        </Card>
    );
}
