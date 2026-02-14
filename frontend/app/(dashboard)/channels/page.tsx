'use client';

import { useState } from 'react';
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
} from 'lucide-react';
import { toast } from 'sonner';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import apiClient from '@/lib/api-client';
import type { Channel } from '@/types';

// ─── Helpers ───────────────────────────────────────────────────────
function StatusBadge({ status }: { status: string }) {
    if (status === 'active') {
        return (
            <Badge variant="outline" className="border-green-500 text-green-600">
                <CheckCircle2 className="mr-1 h-3 w-3" /> Connected
            </Badge>
        );
    }
    return (
        <Badge variant="outline" className="border-yellow-500 text-yellow-600">
            <AlertCircle className="mr-1 h-3 w-3" /> Not Connected
        </Badge>
    );
}

// ─── Page ──────────────────────────────────────────────────────────
export default function ChannelsPage() {
    const queryClient = useQueryClient();

    // Existing channels
    const { data: channels, isLoading } = useQuery({
        queryKey: ['channels'],
        queryFn: async () => {
            const { data } = await apiClient.get<{ data: Channel[] }>('/channels');
            return data.data;
        },
    });

    // Derive existing channels by type
    const whatsappChannel = channels?.find((c) => c.channel_type === 'whatsapp');
    const telegramChannel = channels?.find((c) => c.channel_type === 'telegram');
    const emailChannel = channels?.find((c) => c.channel_type === 'email');

    // ── Save / Create Channel ──
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
            toast.success('Channel saved successfully.');
        },
        onError: (error: unknown) => {
            const message =
                (error as { response?: { data?: { error?: string } } })?.response?.data?.error ||
                'Failed to save channel';
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
                    Channels
                </h2>
                <p className="text-muted-foreground">
                    Connect your messaging channels so your AI agent can talk to your
                    leads automatically.
                </p>
            </div>

            {/* ─── WhatsApp ─── */}
            <WhatsAppCard channel={whatsappChannel} />

            {/* ─── Telegram ─── */}
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

            {/* ─── Email / SMTP ─── */}
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

            {/* ─── Google (Calendar / Gmail) ─── */}
            <GoogleCard />
        </div>
    );
}

// ═══════════════════════════════════════════════════════════════════
// WhatsApp Card (QR-based via api-whatsapp service)
// ═══════════════════════════════════════════════════════════════════
function WhatsAppCard({ channel }: { channel?: Channel }) {
    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
                <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/30">
                        <Smartphone className="h-5 w-5 text-green-600" />
                    </div>
                    <div>
                        <CardTitle className="text-base">WhatsApp</CardTitle>
                        <CardDescription>Connect via QR code scan</CardDescription>
                    </div>
                </div>
                <StatusBadge status={channel?.status || 'inactive'} />
            </CardHeader>
            <CardContent>
                <p className="text-sm text-muted-foreground">
                    WhatsApp connection is managed through the QR code pairing process.
                    Contact your administrator to link a new WhatsApp number, or visit
                    the WhatsApp management panel.
                </p>
                {channel && (
                    <div className="mt-4 rounded-lg border bg-muted/30 p-3 text-sm">
                        <span className="font-medium">Phone:</span>{' '}
                        {(channel.config as Record<string, string>)?.phone_number || 'Connected'}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

// ═══════════════════════════════════════════════════════════════════
// Telegram Card
// ═══════════════════════════════════════════════════════════════════
function TelegramCard({
    channel,
    onSave,
    isSaving,
}: {
    channel?: Channel;
    onSave: (token: string) => void;
    isSaving: boolean;
}) {
    const [token, setToken] = useState('');

    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
                <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/30">
                        <MessageCircle className="h-5 w-5 text-blue-600" />
                    </div>
                    <div>
                        <CardTitle className="text-base">Telegram</CardTitle>
                        <CardDescription>Paste your bot token from @BotFather</CardDescription>
                    </div>
                </div>
                <StatusBadge status={channel?.status || 'inactive'} />
            </CardHeader>
            <CardContent className="space-y-4">
                <div className="space-y-2">
                    <Label htmlFor="telegram_token">Bot Token</Label>
                    <Input
                        id="telegram_token"
                        type="password"
                        placeholder="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
                        value={token}
                        onChange={(e) => setToken(e.target.value)}
                    />
                    <p className="text-xs text-muted-foreground">
                        Get your token from{' '}
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
                    {channel ? 'Update Token' : 'Connect Telegram'}
                </Button>
            </CardContent>
        </Card>
    );
}

// ═══════════════════════════════════════════════════════════════════
// Email / SMTP Card
// ═══════════════════════════════════════════════════════════════════
function EmailCard({
    channel,
    onSave,
    isSaving,
}: {
    channel?: Channel;
    onSave: (creds: Record<string, string>) => void;
    isSaving: boolean;
}) {
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
                        <CardTitle className="text-base">Email (SMTP)</CardTitle>
                        <CardDescription>Send emails from your own address</CardDescription>
                    </div>
                </div>
                <StatusBadge status={channel?.status || 'inactive'} />
            </CardHeader>
            <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                        <Label htmlFor="smtp_host">SMTP Host</Label>
                        <Input
                            id="smtp_host"
                            placeholder="smtp.gmail.com"
                            value={host}
                            onChange={(e) => setHost(e.target.value)}
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="smtp_port">Port</Label>
                        <Input
                            id="smtp_port"
                            placeholder="587"
                            value={port}
                            onChange={(e) => setPort(e.target.value)}
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="smtp_user">Email / Username</Label>
                        <Input
                            id="smtp_user"
                            placeholder="you@gmail.com"
                            value={user}
                            onChange={(e) => setUser(e.target.value)}
                        />
                    </div>
                    <div className="space-y-2">
                        <Label htmlFor="smtp_pass">Password / App Password</Label>
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
                    {channel ? 'Update SMTP' : 'Connect Email'}
                </Button>
            </CardContent>
        </Card>
    );
}

// ═══════════════════════════════════════════════════════════════════
// Google Card (Calendar / Gmail OAuth)
// ═══════════════════════════════════════════════════════════════════
function GoogleCard() {
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
            // Open in same window (will redirect back after OAuth)
            window.location.href = data.data.authorization_url;
        } catch {
            toast.error('Google login is not configured yet. Contact your administrator.');
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
                        <CardTitle className="text-base">Google</CardTitle>
                        <CardDescription>Calendar &amp; Gmail integration</CardDescription>
                    </div>
                </div>
                <StatusBadge status={isConnected ? 'active' : 'inactive'} />
            </CardHeader>
            <CardContent>
                {isConnected ? (
                    <p className="text-sm text-green-600">
                        ✓ Google account connected. Calendar scheduling and Gmail are
                        available.
                    </p>
                ) : (
                    <>
                        <p className="mb-4 text-sm text-muted-foreground">
                            Connect your Google account to enable automatic meeting
                            scheduling (Google Calendar) and email sending (Gmail).
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
                            Sign in with Google
                        </Button>
                    </>
                )}
            </CardContent>
        </Card>
    );
}
