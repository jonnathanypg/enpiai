'use client';

import { use } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
    User,
    Phone,
    Mail,
    MapPin,
    Calendar,
    MoreVertical,
    MessageSquare,
    FileText,
    Activity,
    ArrowLeft,
    Send,
    Trash2,
} from 'lucide-react';
import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import Link from 'next/link';
import { format } from 'date-fns';
import { useTranslation } from 'react-i18next';

import { Button } from '@/components/ui/button';
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { LeadTimeline } from '@/components/features/lead-timeline';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Switch } from '@/components/ui/switch';
import apiClient from '@/lib/api-client';
import type { UnifiedContact } from '@/types';

export default function UnifiedContactPage({ params }: { params: Promise<{ id: string }> }) {
    const { id } = use(params);
    const { t } = useTranslation();
    const queryClient = useQueryClient();
    const [noteContent, setNoteContent] = useState('');
    const [activeTab, setActiveTab] = useState('timeline');

    const { data: contact, isLoading } = useQuery({
        queryKey: ['unified-contact', id],
        queryFn: async () => {
            const { data } = await apiClient.get<{ data: UnifiedContact }>(`/contacts/unified/${id}`);
            return data.data;
        },
    });

    const addNoteMutation = useMutation({
        mutationFn: async (content: string) => {
            return apiClient.post(`/contacts/unified/${id}/notes`, { content });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['unified-contact', id] });
            setNoteContent('');
            toast.success('Note added successfully');
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.error || 'Failed to add note');
        },
    });

    const toggleAiMutation = useMutation({
        mutationFn: async (isActive: boolean) => {
            return apiClient.put(`/contacts/unified/${id}/ai-toggle`, { is_ai_active: isActive });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['unified-contact', id] });
            toast.success('AI response setting updated');
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.error || 'Failed to update AI setting');
        },
    });

    const deleteLeadMutation = useMutation({
        mutationFn: async () => {
            const leadId = contact?.lead?.id;
            if (!leadId) throw new Error('Lead ID not found');
            return apiClient.delete(`/evaluations/leads/${leadId}`);
        },
        onSuccess: () => {
            toast.success('Contact deleted successfully');
            window.location.href = '/contacts';
        },
    });

    if (isLoading) {
        return <div className="space-y-4"><Skeleton className="h-48 w-full" /><Skeleton className="h-96 w-full" /></div>;
    }

    if (!contact) {
        return <div>Contact not found</div>;
    }

    const profile = contact.lead || contact.customer;
    if (!profile) return <div>Invalid contact data</div>;

    const initials = `${profile.first_name?.[0] || ''}${profile.last_name?.[0] || ''}`;
    const statusColor = profile.status === 'qualified' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700';
    const evals = contact.evaluations || [];

    return (
        <div className="space-y-6">
            {/* Header / Breadcrumb */}
            <div className="flex items-center gap-2">
                <Link href="/contacts">
                    <Button variant="ghost" size="icon">
                        <ArrowLeft className="h-4 w-4" />
                    </Button>
                </Link>
                <h1 className="text-xl font-semibold">{t('wellness.profile')}</h1>
            </div>

            <div className="grid gap-6 lg:grid-cols-12">
                {/* Left Column: Profile Card */}
                <div className="lg:col-span-4 space-y-6">
                    <Card>
                        <CardContent className="pt-6">
                            <div className="flex flex-col items-center text-center">
                                <Avatar className="h-24 w-24">
                                    <AvatarImage src="" />
                                    <AvatarFallback className="text-2xl">{initials}</AvatarFallback>
                                </Avatar>
                                <h2 className="mt-4 text-xl font-bold">
                                    {profile.first_name} {profile.last_name}
                                </h2>
                                <Badge variant="secondary" className="mt-2 capitalize">
                                    {/* Handle specific status logic from UnifiedContact resolver */}
                                    {profile.status}
                                </Badge>

                                <div className="mt-6 w-full space-y-4 text-left">
                                    <div className="flex items-center gap-3 text-sm">
                                        <Mail className="h-4 w-4 text-muted-foreground" />
                                        <span>{profile.email || 'No email'}</span>
                                    </div>
                                    <div className="flex items-center gap-3 text-sm">
                                        <Phone className="h-4 w-4 text-muted-foreground" />
                                        <span>{profile.phone || 'No phone'}</span>
                                    </div>
                                    <div className="flex items-center gap-3 text-sm">
                                        <Calendar className="h-4 w-4 text-muted-foreground" />
                                        <span>Added {format(new Date(profile.created_at), 'PPP')}</span>
                                    </div>

                                    <Separator className="my-4" />
                                    
                                    <div className="flex items-center justify-between">
                                        <div className="space-y-0.5">
                                            <Label className="text-sm font-medium">Auto AI Responses</Label>
                                            <p className="text-xs text-muted-foreground">Allow AI to auto-reply to this contact</p>
                                        </div>
                                        <Switch 
                                            checked={profile.is_ai_active ?? true} 
                                            onCheckedChange={(checked) => toggleAiMutation.mutate(checked)}
                                            disabled={toggleAiMutation.isPending}
                                        />
                                    </div>
                                </div>

                                <div className="mt-8 flex w-full gap-2">
                                    <DropdownMenu>
                                        <DropdownMenuTrigger asChild>
                                            <Button className="flex-1">
                                                <MessageSquare className="mr-2 h-4 w-4" /> Message
                                            </Button>
                                        </DropdownMenuTrigger>
                                        <DropdownMenuContent align="end">
                                            <DropdownMenuItem onClick={() => {
                                                const phone = profile.phone?.replace(/\D/g, '');
                                                if (phone) window.open(`https://wa.me/${phone}`, '_blank');
                                                else toast.error('No phone number available');
                                            }}>
                                                WhatsApp
                                            </DropdownMenuItem>
                                            <DropdownMenuItem onClick={() => {
                                                if (profile.email) window.location.href = `mailto:${profile.email}`;
                                                else toast.error('No email address available');
                                            }}>
                                                Email
                                            </DropdownMenuItem>
                                        </DropdownMenuContent>
                                    </DropdownMenu>

                                    <DropdownMenu>
                                        <DropdownMenuTrigger asChild>
                                            <Button variant="outline" size="icon">
                                                <MoreVertical className="h-4 w-4" />
                                            </Button>
                                        </DropdownMenuTrigger>
                                        <DropdownMenuContent align="end">
                                            <DropdownMenuItem className="text-destructive" onClick={() => {
                                                if (confirm('Are you sure you want to delete this contact?')) {
                                                    deleteLeadMutation.mutate();
                                                }
                                            }}>
                                                <Trash2 className="mr-2 h-4 w-4" /> Delete Contact
                                            </DropdownMenuItem>
                                        </DropdownMenuContent>
                                    </DropdownMenu>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Wellness Summary (If available) */}
                    {evals.length > 0 && (
                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2 text-base">
                                    <Activity className="h-4 w-4" /> {t('wellness.stats')}
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-2 text-sm">
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">Latest BMI:</span>
                                    <span className="font-bold">{evals[0].bmi?.toFixed(1) || 'N/A'}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">Goal:</span>
                                    <span>{evals[0].primary_goal || 'None'}</span>
                                </div>
                                <Button 
                                    variant="link" 
                                    className="px-0 text-primary"
                                    onClick={() => setActiveTab('wellness')}
                                >
                                    {t('wellness.viewFullReport')}
                                </Button>
                            </CardContent>
                        </Card>
                    )}
                </div>

                {/* Right Column: Timeline & Tabs */}
                <div className="lg:col-span-8">
                    <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                        <TabsList className="grid w-full grid-cols-3">
                            <TabsTrigger value="timeline">{t('wellness.timeline')}</TabsTrigger>
                            <TabsTrigger value="wellness">Wellness</TabsTrigger>
                            <TabsTrigger value="notes">{t('wellness.notes')}</TabsTrigger>
                        </TabsList>

                        <TabsContent value="timeline" className="mt-6">
                            <Card>
                                <CardHeader>
                                    <CardTitle>{t('wellness.interactionHistory')}</CardTitle>
                                    <CardDescription>
                                        {t('wellness.timelineDescription')}
                                    </CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <LeadTimeline
                                        conversations={contact.conversations}
                                        appointments={contact.appointments}
                                        evaluations={contact.evaluations}
                                        notes={contact.notes}
                                    />
                                </CardContent>
                            </Card>
                        </TabsContent>

                        <TabsContent value="wellness" className="mt-6">
                            <div className="space-y-6">
                                {evals.length === 0 ? (
                                    <div className="flex h-64 items-center justify-center rounded-lg border border-dashed text-muted-foreground">
                                        <p>{t('wellness.noEvaluations')}</p>
                                    </div>
                                ) : (
                                    evals.map((ev) => (
                                        <Card key={ev.id}>
                                            <CardHeader className="pb-3">
                                                <div className="flex items-center justify-between">
                                                    <div>
                                                        <CardTitle className="text-lg">
                                                            {t('wellness.evaluation')} #{ev.id}
                                                        </CardTitle>
                                                        <CardDescription>
                                                            {format(new Date(ev.created_at), 'PPP')}
                                                        </CardDescription>
                                                    </div>
                                                    <Badge variant={ev.bmi && ev.bmi > 25 ? 'destructive' : 'default'} className="text-sm">
                                                        BMI: {ev.bmi?.toFixed(1) || 'N/A'}
                                                    </Badge>
                                                </div>
                                            </CardHeader>
                                            <CardContent className="space-y-4">
                                                <div className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
                                                    <div className="space-y-1">
                                                        <p className="text-muted-foreground">Weight</p>
                                                        <p className="font-medium">{ev.weight_kg} kg</p>
                                                    </div>
                                                    <div className="space-y-1">
                                                        <p className="text-muted-foreground">Height</p>
                                                        <p className="font-medium">{ev.height_cm} cm</p>
                                                    </div>
                                                    <div className="space-y-1">
                                                        <p className="text-muted-foreground">Goal</p>
                                                        <p className="font-medium">{ev.primary_goal}</p>
                                                    </div>
                                                    <div className="space-y-1">
                                                        <p className="text-muted-foreground">Energy</p>
                                                        <p className="font-medium">{ev.energy_level}/10</p>
                                                    </div>
                                                </div>
                                                
                                                {ev.diagnosis && (
                                                    <div className="rounded-lg bg-primary/5 p-4 border border-primary/10">
                                                        <h4 className="flex items-center gap-2 font-bold mb-2">
                                                            <Activity className="h-4 w-4 text-primary" /> Diagnóstico AI
                                                        </h4>
                                                        <p className="text-sm whitespace-pre-wrap leading-relaxed">{ev.diagnosis}</p>
                                                    </div>
                                                )}

                                                {ev.recommendations && (
                                                    <div className="rounded-lg bg-green-50 p-4 border border-green-100">
                                                        <h4 className="flex items-center gap-2 font-bold mb-2 text-green-800">
                                                            <FileText className="h-4 w-4 text-green-600" /> Recomendaciones
                                                        </h4>
                                                        <p className="text-sm whitespace-pre-wrap leading-relaxed text-green-900">{ev.recommendations}</p>
                                                    </div>
                                                )}
                                                
                                                {ev.pdf_report_path && (
                                                    <Button 
                                                        variant="outline" 
                                                        className="w-full sm:w-auto"
                                                        onClick={() => {
                                                            const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api';
                                                            const cleanBase = apiBase.replace('/api', '');
                                                            window.open(`${cleanBase}/api/wellness/reports/${ev.pdf_report_path}`, '_blank');
                                                        }}
                                                    >
                                                        <FileText className="mr-2 h-4 w-4" /> Download Report
                                                    </Button>
                                                )}
                                            </CardContent>
                                        </Card>
                                    ))
                                )}
                            </div>
                        </TabsContent>
                        <TabsContent value="notes" className="mt-6">
                            <div className="space-y-6">
                                <Card>
                                    <CardHeader>
                                        <CardTitle className="text-base">{t('wellness.notes')}</CardTitle>
                                        <CardDescription>Añade comentarios o recordatorios sobre este contacto.</CardDescription>
                                    </CardHeader>
                                    <CardContent className="space-y-4">
                                        <div className="space-y-2">
                                            <Label htmlFor="note">Nueva Nota</Label>
                                            <Textarea 
                                                id="note" 
                                                placeholder="Escribe algo importante..." 
                                                value={noteContent}
                                                onChange={(e) => setNoteContent(e.target.value)}
                                                className="min-h-[100px]"
                                            />
                                        </div>
                                        <Button 
                                            onClick={() => addNoteMutation.mutate(noteContent)}
                                            disabled={!noteContent.trim() || addNoteMutation.isPending}
                                            className="w-full sm:w-auto"
                                        >
                                            {addNoteMutation.isPending ? 'Guardando...' : <><Send className="mr-2 h-4 w-4" /> Guardar Nota</>}
                                        </Button>
                                    </CardContent>
                                </Card>

                                <div className="space-y-4">
                                    {(!contact || !contact.notes || contact.notes.length === 0) ? (
                                        <div className="flex h-32 items-center justify-center rounded-lg border border-dashed text-muted-foreground">
                                            <p>No hay notas registradas.</p>
                                        </div>
                                    ) : (
                                        contact.notes.map((note) => (
                                            <Card key={note.id}>
                                                <CardContent className="pt-6">
                                                    <div className="flex items-center justify-between mb-2">
                                                        <span className="text-xs font-semibold text-primary uppercase tracking-wider">
                                                            {note.author_name || 'Agente'}
                                                        </span>
                                                        <time className="text-xs text-muted-foreground">
                                                            {format(new Date(note.created_at), 'PPP p')}
                                                        </time>
                                                    </div>
                                                    <p className="text-sm whitespace-pre-wrap">{note.content}</p>
                                                </CardContent>
                                            </Card>
                                        ))
                                    )}
                                </div>
                            </div>
                        </TabsContent>
                    </Tabs>
                </div>
            </div>
        </div>
    );
}
