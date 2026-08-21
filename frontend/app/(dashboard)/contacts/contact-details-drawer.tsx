'use client';

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
    Phone, Mail, Calendar, MessageSquare, Send, Trash2,
    FileText, CalendarCheck, Activity, Award, UserCheck, 
    Bot, MoreVertical, MapPin, Edit, Check, X, ShieldAlert
} from 'lucide-react';
import { toast } from 'sonner';
import { format } from 'date-fns';
import { useTranslation } from 'react-i18next';

import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { LeadTimeline } from '@/components/features/lead-timeline';
import apiClient from '@/lib/api-client';
import type { UnifiedContact } from '@/types';

interface ContactDetailsDrawerProps {
    contactId: number | null;
    isOpen: boolean;
    onClose: () => void;
    onUpdate?: () => void;
}

const formatDateSafe = (dateString: string | Date | null | undefined, formatStr: string) => {
    if (!dateString) return 'N/A';
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return 'N/A';
    return format(d, formatStr);
};

export default function ContactDetailsDrawer({ contactId, isOpen, onClose, onUpdate }: ContactDetailsDrawerProps) {
    const { t } = useTranslation();
    const queryClient = useQueryClient();
    const [noteContent, setNoteContent] = useState('');
    const [activeTab, setActiveTab] = useState('timeline');
    const [isEditing, setIsEditing] = useState(false);

    // Edit Form State
    const [editForm, setEditForm] = useState({
        first_name: '',
        last_name: '',
        email: '',
        phone: '',
        city: '',
        country: '',
        status: 'new',
        lead_type: 'unknown',
    });

    // 1. Fetch Unified Contact Details
    const { data: contact, isLoading, error } = useQuery({
        queryKey: ['unified-contact', contactId],
        queryFn: async () => {
            if (!contactId) return null;
            const { data } = await apiClient.get<{ data: UnifiedContact }>(`/contacts/unified/${contactId}`);
            return data.data;
        },
        enabled: !!contactId && isOpen,
    });

    const profile = contact?.lead || contact?.customer;

    // Populate Edit Form when Contact is fetched
    useEffect(() => {
        if (profile) {
            setEditForm({
                first_name: profile.first_name || '',
                last_name: profile.last_name || '',
                email: profile.email || '',
                phone: profile.phone || '',
                city: (profile as any).city || '',
                country: (profile as any).country || '',
                status: profile.status || 'new',
                lead_type: (profile as any).lead_type || 'unknown',
            });
        }
        setIsEditing(false);
    }, [contact, profile]);

    // 2. Add Note Mutation
    const addNoteMutation = useMutation({
        mutationFn: async (content: string) => {
            if (!contactId) return null;
            return apiClient.post(`/contacts/unified/${contactId}/notes`, { content });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['unified-contact', contactId] });
            setNoteContent('');
            toast.success(t('contacts.noteAdded', { defaultValue: 'Note added successfully' }));
            onUpdate?.();
        },
        onError: (err: any) => toast.error(err.response?.data?.error || t('common.error')),
    });

    // 3. Toggle AI Mutation
    const toggleAiMutation = useMutation({
        mutationFn: async (isActive: boolean) => {
            if (!contactId) return null;
            return apiClient.put(`/contacts/unified/${contactId}/ai-toggle`, { is_ai_active: isActive });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['unified-contact', contactId] });
            toast.success(t('common.success', { defaultValue: 'AI settings updated' }));
            onUpdate?.();
        },
        onError: (err: any) => toast.error(err.response?.data?.error || t('common.error')),
    });

    // 4. Update Lead Mutation
    const updateLeadMutation = useMutation({
        mutationFn: async (formData: typeof editForm) => {
            const leadId = contact?.lead?.id;
            if (!leadId) throw new Error('Lead ID not found');
            return apiClient.put(`/leads/${leadId}`, formData);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['unified-contact', contactId] });
            setIsEditing(false);
            toast.success(t('common.success', { defaultValue: 'Profile updated successfully' }));
            onUpdate?.();
        },
        onError: (err: any) => {
            toast.error(err.response?.data?.error || t('common.error'));
        },
    });

    // 5. Delete Lead Mutation
    const deleteLeadMutation = useMutation({
        mutationFn: async () => {
            const leadId = contact?.lead?.id;
            if (!leadId) throw new Error('Lead ID not found');
            return apiClient.delete(`/leads/${leadId}`);
        },
        onSuccess: () => {
            toast.success(t('common.success', { defaultValue: 'Contact deleted successfully' }));
            onClose();
            onUpdate?.();
        },
        onError: (err: any) => {
            toast.error(err.response?.data?.error || t('common.error'));
        },
    });

    const initials = profile ? `${profile.first_name?.[0] || ''}${profile.last_name?.[0] || ''}`.toUpperCase() : '';
    const fullName = profile ? `${profile.first_name || ''} ${profile.last_name || ''}`.trim() || profile.phone || t('contacts.noName', { defaultValue: 'Desconocido' }) : '';
    const score = profile ? (profile as any).score ?? (profile as any).metadata?.score ?? 0 : 0;
    const evals = contact?.evaluations || [];

    return (
        <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <SheetContent side="right" className="sm:max-w-xl md:max-w-2xl w-full h-full overflow-y-auto p-0 flex flex-col bg-background border-l shadow-2xl">
                <SheetHeader className="p-6 border-b bg-muted/20 shrink-0">
                    <div className="flex justify-between items-center pr-6">
                        <div>
                            <SheetTitle className="text-xl font-bold flex items-center gap-2">
                                <UserCheck className="h-5 w-5 text-primary" />
                                {t('contacts.sheetTitle', { defaultValue: 'Detalles del Prospecto' })}
                            </SheetTitle>
                            <SheetDescription>
                                {t('contacts.sheetDesc', { defaultValue: 'Ver y actualizar los datos de perfil del prospecto, puntuación e historial.' })}
                            </SheetDescription>
                        </div>
                    </div>
                </SheetHeader>

                <div className="flex-1 overflow-y-auto min-h-0">
                    {isLoading ? (
                        <div className="p-6 space-y-6">
                            <div className="flex items-center gap-4">
                                <Skeleton className="h-16 w-16 rounded-full" />
                                <div className="space-y-2 flex-1">
                                    <Skeleton className="h-6 w-1/3" />
                                    <Skeleton className="h-4 w-1/4" />
                                </div>
                            </div>
                            <Skeleton className="h-48 w-full rounded-2xl" />
                            <Skeleton className="h-64 w-full rounded-2xl" />
                        </div>
                    ) : error || !contact || !profile ? (
                        <div className="p-12 text-center text-muted-foreground">
                            <p>{t('contacts.notFound', { defaultValue: 'Contacto no encontrado' })}</p>
                            <Button variant="outline" size="sm" onClick={onClose} className="mt-4">
                                {t('common.close', { defaultValue: 'Cerrar' })}
                            </Button>
                        </div>
                    ) : (
                        <div className="p-6 space-y-6">
                            {/* Profile Header Block */}
                            <div className="flex flex-col sm:flex-row items-center sm:items-start justify-between gap-4 p-5 rounded-2xl border bg-card/50">
                                <div className="flex flex-col sm:flex-row items-center gap-4 text-center sm:text-left">
                                    <Avatar className="h-16 w-16 ring-2 ring-primary/10">
                                        <AvatarFallback className="text-xl font-bold bg-primary/5 text-primary">{initials}</AvatarFallback>
                                    </Avatar>
                                    <div>
                                        <h2 className="text-lg font-bold text-foreground">{fullName}</h2>
                                        <div className="flex flex-wrap justify-center sm:justify-start gap-1.5 mt-1.5">
                                            <Badge variant="secondary" className="capitalize text-[10px] py-0.5 px-2">
                                                {profile.status || 'new'}
                                            </Badge>
                                            
                                            {/* Score Badge */}
                                            <Badge 
                                                className={`text-[10px] py-0.5 px-2 border-0 font-bold ${
                                                    score >= 80 
                                                        ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950' 
                                                        : score >= 50 
                                                            ? 'bg-amber-100 text-amber-800 dark:bg-amber-950'
                                                            : 'bg-slate-100 text-slate-800 dark:bg-slate-800'
                                                }`}
                                            >
                                                <Award className="h-3 w-3 mr-1 shrink-0" />
                                                {score} pts
                                            </Badge>
                                        </div>
                                    </div>
                                </div>

                                <div className="flex gap-2">
                                    <Button 
                                        variant={isEditing ? "ghost" : "outline"} 
                                        size="sm" 
                                        onClick={() => setIsEditing(!isEditing)}
                                        className="h-8 gap-1.5"
                                    >
                                        {isEditing ? (
                                            <>
                                                <X className="h-3.5 w-3.5" />
                                                {t('common.cancel', { defaultValue: 'Cancelar' })}
                                            </>
                                        ) : (
                                            <>
                                                <Edit className="h-3.5 w-3.5" />
                                                {t('common.edit', { defaultValue: 'Editar' })}
                                            </>
                                        )}
                                    </Button>

                                    <DropdownMenu>
                                        <DropdownMenuTrigger asChild>
                                            <Button variant="outline" size="icon" className="h-8 w-8">
                                                <MoreVertical className="h-4 w-4" />
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
                                            <DropdownMenuItem className="text-destructive focus:text-destructive" onClick={() => {
                                                if (confirm(t('common.confirmDelete', { defaultValue: 'Are you sure you want to delete this contact?' }))) {
                                                    deleteLeadMutation.mutate();
                                                }
                                            }}>
                                                <Trash2 className="mr-2 h-4 w-4" />
                                                {t('common.delete', { defaultValue: 'Eliminar' })}
                                            </DropdownMenuItem>
                                        </DropdownMenuContent>
                                    </DropdownMenu>
                                </div>
                            </div>

                            {isEditing ? (
                                /* Profiling/Edit Form */
                                <Card className="border shadow-sm rounded-2xl">
                                    <CardHeader>
                                        <CardTitle className="text-sm font-bold">{t('contacts.editProfile', { defaultValue: 'Editar Perfil del Prospecto' })}</CardTitle>
                                    </CardHeader>
                                    <CardContent className="space-y-4">
                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="space-y-1">
                                                <Label htmlFor="first_name" className="text-xs">{t('common.firstName', { defaultValue: 'Nombre' })}</Label>
                                                <Input 
                                                    id="first_name" 
                                                    value={editForm.first_name} 
                                                    onChange={e => setEditForm({ ...editForm, first_name: e.target.value })} 
                                                />
                                            </div>
                                            <div className="space-y-1">
                                                <Label htmlFor="last_name" className="text-xs">{t('common.lastName', { defaultValue: 'Apellido' })}</Label>
                                                <Input 
                                                    id="last_name" 
                                                    value={editForm.last_name} 
                                                    onChange={e => setEditForm({ ...editForm, last_name: e.target.value })} 
                                                />
                                            </div>
                                        </div>

                                        <div className="space-y-1">
                                            <Label htmlFor="email" className="text-xs">{t('common.email')}</Label>
                                            <Input 
                                                id="email" 
                                                type="email" 
                                                value={editForm.email} 
                                                onChange={e => setEditForm({ ...editForm, email: e.target.value })} 
                                            />
                                        </div>

                                        <div className="space-y-1">
                                            <Label htmlFor="phone" className="text-xs">{t('common.phone', { defaultValue: 'Teléfono' })}</Label>
                                            <Input 
                                                id="phone" 
                                                value={editForm.phone} 
                                                onChange={e => setEditForm({ ...editForm, phone: e.target.value })} 
                                            />
                                        </div>

                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="space-y-1">
                                                <Label htmlFor="city" className="text-xs">{t('common.city', { defaultValue: 'Ciudad' })}</Label>
                                                <Input 
                                                    id="city" 
                                                    value={editForm.city} 
                                                    onChange={e => setEditForm({ ...editForm, city: e.target.value })} 
                                                />
                                            </div>
                                            <div className="space-y-1">
                                                <Label htmlFor="country" className="text-xs">{t('common.country', { defaultValue: 'País' })}</Label>
                                                <Input 
                                                    id="country" 
                                                    value={editForm.country} 
                                                    onChange={e => setEditForm({ ...editForm, country: e.target.value })} 
                                                />
                                            </div>
                                        </div>

                                        <div className="grid grid-cols-2 gap-4">
                                            <div className="space-y-1">
                                                <Label htmlFor="status" className="text-xs">{t('common.status')}</Label>
                                                <Select 
                                                    value={editForm.status} 
                                                    onValueChange={val => setEditForm({ ...editForm, status: val })}
                                                >
                                                    <SelectTrigger>
                                                        <SelectValue />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        <SelectItem value="new">Nuevo</SelectItem>
                                                        <SelectItem value="contacted">Contactado</SelectItem>
                                                        <SelectItem value="qualified">Calificado</SelectItem>
                                                        <SelectItem value="nurturing">En Seguimiento</SelectItem>
                                                        <SelectItem value="converted">Convertido</SelectItem>
                                                        <SelectItem value="lost">Perdido</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                            </div>

                                            <div className="space-y-1">
                                                <Label htmlFor="lead_type" className="text-xs">{t('common.leadType', { defaultValue: 'Tipo' })}</Label>
                                                <Select 
                                                    value={editForm.lead_type} 
                                                    onValueChange={val => setEditForm({ ...editForm, lead_type: val })}
                                                >
                                                    <SelectTrigger>
                                                        <SelectValue />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        <SelectItem value="product_interest">Interés en Productos</SelectItem>
                                                        <SelectItem value="business_opportunity">Oportunidad de Negocio</SelectItem>
                                                        <SelectItem value="unknown">Desconocido</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                        </div>

                                        <div className="pt-2 flex justify-end gap-2">
                                            <Button 
                                                variant="outline" 
                                                onClick={() => setIsEditing(false)}
                                                disabled={updateLeadMutation.isPending}
                                            >
                                                {t('common.cancel', { defaultValue: 'Cancelar' })}
                                            </Button>
                                            <Button 
                                                onClick={() => updateLeadMutation.mutate(editForm)}
                                                disabled={updateLeadMutation.isPending}
                                                className="gap-1.5"
                                            >
                                                <Check className="h-4 w-4" />
                                                {updateLeadMutation.isPending ? t('common.saving', { defaultValue: 'Guardando...' }) : t('common.save', { defaultValue: 'Guardar' })}
                                            </Button>
                                        </div>
                                    </CardContent>
                                </Card>
                            ) : (
                                <>
                                    {/* AI Agent Auto-Response Settings */}
                                    <div className="flex items-center justify-between p-4 bg-muted/20 rounded-2xl border">
                                        <div className="space-y-0.5">
                                            <Label className="text-sm font-semibold flex items-center gap-1.5">
                                                <Bot className="h-4 w-4 text-primary" />
                                                {t('contacts.aiAutoResponse', { defaultValue: 'Auto-Respuestas de IA' })}
                                            </Label>
                                            <p className="text-xs text-muted-foreground">
                                                {t('contacts.aiAutoResponseDesc', { defaultValue: 'Permitir que el agente responda automáticamente a este contacto.' })}
                                            </p>
                                        </div>
                                        <Switch 
                                            checked={profile.is_ai_active ?? true} 
                                            onCheckedChange={(checked) => toggleAiMutation.mutate(checked)}
                                            disabled={toggleAiMutation.isPending}
                                        />
                                    </div>

                                    {/* Tabs Section */}
                                    <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                                        <TabsList className="grid w-full grid-cols-4">
                                            <TabsTrigger value="timeline" className="text-xs">{t('wellness.timeline', { defaultValue: 'Historial' })}</TabsTrigger>
                                            <TabsTrigger value="wellness" className="text-xs">Wellness</TabsTrigger>
                                            <TabsTrigger value="notes" className="text-xs">{t('wellness.notes', { defaultValue: 'Notas' })}</TabsTrigger>
                                            <TabsTrigger value="profile" className="text-xs">{t('common.profile', { defaultValue: 'Detalles' })}</TabsTrigger>
                                        </TabsList>

                                        {/* Timeline Tab */}
                                        <TabsContent value="timeline" className="mt-4">
                                            <Card className="border rounded-2xl bg-card">
                                                <CardHeader className="pb-2">
                                                    <CardTitle className="text-base font-bold">{t('wellness.interactionHistory', { defaultValue: 'Historial de Interacción' })}</CardTitle>
                                                    <CardDescription className="text-xs">
                                                        {t('wellness.timelineDescription', { defaultValue: 'Línea de tiempo de mensajes, evaluaciones y citas.' })}
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

                                        {/* Wellness Evaluations Tab */}
                                        <TabsContent value="wellness" className="mt-4">
                                            <div className="space-y-4">
                                                {evals.length === 0 ? (
                                                    <div className="flex h-48 items-center justify-center rounded-2xl border border-dashed text-muted-foreground p-6 text-center text-sm">
                                                        <div>
                                                            <Activity className="h-8 w-8 mx-auto opacity-20 mb-2" />
                                                            <p>{t('wellness.noEvaluations', { defaultValue: 'No hay evaluaciones de bienestar registradas.' })}</p>
                                                        </div>
                                                    </div>
                                                ) : (
                                                    evals.map((ev) => (
                                                        <Card key={ev.id} className="border rounded-2xl bg-card">
                                                            <CardHeader className="pb-3">
                                                                <div className="flex items-center justify-between">
                                                                    <div>
                                                                        <CardTitle className="text-sm font-bold">
                                                                            {t('wellness.evaluation', { defaultValue: 'Evaluación de Bienestar' })} #{ev.id}
                                                                        </CardTitle>
                                                                        <CardDescription className="text-xs">
                                                                            {formatDateSafe(ev.created_at, 'PPP')}
                                                                        </CardDescription>
                                                                    </div>
                                                                    <Badge variant={ev.bmi && ev.bmi > 25 ? 'destructive' : 'default'} className="text-[10px]">
                                                                        BMI: {ev.bmi?.toFixed(1) || 'N/A'}
                                                                    </Badge>
                                                                </div>
                                                            </CardHeader>
                                                            <CardContent className="space-y-4 text-xs">
                                                                <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 bg-muted/20 p-3 rounded-xl">
                                                                    <div className="space-y-0.5">
                                                                        <p className="text-muted-foreground text-[10px]">Peso</p>
                                                                        <p className="font-bold text-foreground">{ev.weight_kg} kg</p>
                                                                    </div>
                                                                    <div className="space-y-0.5">
                                                                        <p className="text-muted-foreground text-[10px]">Altura</p>
                                                                        <p className="font-bold text-foreground">{ev.height_cm} cm</p>
                                                                    </div>
                                                                    <div className="space-y-0.5">
                                                                        <p className="text-muted-foreground text-[10px]">Objetivo</p>
                                                                        <p className="font-bold text-foreground">{ev.primary_goal}</p>
                                                                    </div>
                                                                    <div className="space-y-0.5">
                                                                        <p className="text-muted-foreground text-[10px]">Energía</p>
                                                                        <p className="font-bold text-foreground">{ev.energy_level}/10</p>
                                                                    </div>
                                                                </div>
                                                                
                                                                {ev.diagnosis && (
                                                                    <div className="rounded-xl bg-primary/5 p-3.5 border border-primary/10">
                                                                        <h4 className="flex items-center gap-1.5 font-bold mb-1.5 text-foreground text-xs">
                                                                            <Activity className="h-3.5 w-3.5 text-primary" /> Diagnóstico AI
                                                                        </h4>
                                                                        <p className="text-xs whitespace-pre-wrap leading-relaxed text-foreground/80">{ev.diagnosis}</p>
                                                                    </div>
                                                                )}

                                                                {ev.recommendations && (
                                                                    <div className="rounded-xl bg-green-50/50 dark:bg-green-950/20 p-3.5 border border-green-100/10">
                                                                        <h4 className="flex items-center gap-1.5 font-bold mb-1.5 text-green-800 dark:text-green-300 text-xs">
                                                                            <FileText className="h-3.5 w-3.5 text-green-600 dark:text-green-400" /> Recomendaciones
                                                                        </h4>
                                                                        <p className="text-xs whitespace-pre-wrap leading-relaxed text-green-900 dark:text-green-100">{ev.recommendations}</p>
                                                                    </div>
                                                                )}
                                                                
                                                                {ev.pdf_report_path && (
                                                                    <Button 
                                                                        variant="outline" 
                                                                        size="sm"
                                                                        className="w-full text-xs h-8"
                                                                        onClick={() => {
                                                                            const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api';
                                                                            const cleanBase = apiBase.replace('/api', '');
                                                                            window.open(`${cleanBase}/api/wellness/reports/${ev.pdf_report_path}`, '_blank');
                                                                        }}
                                                                    >
                                                                        <FileText className="mr-1.5 h-3.5 w-3.5" /> Download Report
                                                                    </Button>
                                                                )}
                                                            </CardContent>
                                                        </Card>
                                                    ))
                                                )}
                                            </div>
                                        </TabsContent>

                                        {/* Notes Tab */}
                                        <TabsContent value="notes" className="mt-4">
                                            <div className="space-y-4">
                                                <Card className="border rounded-2xl bg-card">
                                                    <CardHeader className="pb-3">
                                                        <CardTitle className="text-sm font-bold">{t('wellness.notes')}</CardTitle>
                                                        <CardDescription className="text-xs">Añade comentarios o recordatorios sobre este contacto.</CardDescription>
                                                    </CardHeader>
                                                    <CardContent className="space-y-3">
                                                        <Textarea 
                                                            placeholder="Escribe algo importante..." 
                                                            value={noteContent}
                                                            onChange={(e) => setNoteContent(e.target.value)}
                                                            className="min-h-[80px] text-xs bg-background"
                                                        />
                                                        <Button 
                                                            size="sm"
                                                            onClick={() => addNoteMutation.mutate(noteContent)}
                                                            disabled={!noteContent.trim() || addNoteMutation.isPending}
                                                            className="w-full sm:w-auto h-8 text-xs"
                                                        >
                                                            {addNoteMutation.isPending ? 'Guardando...' : <><Send className="mr-1.5 h-3.5 w-3.5" /> Guardar Nota</>}
                                                        </Button>
                                                    </CardContent>
                                                </Card>

                                                <div className="space-y-3">
                                                    {(!contact.notes || contact.notes.length === 0) ? (
                                                        <div className="flex h-24 items-center justify-center rounded-2xl border border-dashed text-muted-foreground text-xs">
                                                            <p>No hay notas registradas.</p>
                                                        </div>
                                                    ) : (
                                                        contact.notes.map((note) => (
                                                            <Card key={note.id} className="border rounded-2xl bg-card">
                                                                <CardContent className="pt-4 pb-4">
                                                                    <div className="flex items-center justify-between mb-1.5">
                                                                        <span className="text-[10px] font-bold text-primary uppercase tracking-wider">
                                                                            {note.author_name || 'Agente'}
                                                                        </span>
                                                                        <time className="text-[10px] text-muted-foreground">
                                                                            {formatDateSafe(note.created_at, 'PPP p')}
                                                                        </time>
                                                                    </div>
                                                                    <p className="text-xs whitespace-pre-wrap leading-relaxed text-foreground/90">{note.content}</p>
                                                                </CardContent>
                                                            </Card>
                                                        ))
                                                    )}
                                                </div>
                                            </div>
                                        </TabsContent>

                                        {/* Static Profile Tab */}
                                        <TabsContent value="profile" className="mt-4">
                                            <Card className="border rounded-2xl bg-card">
                                                <CardHeader>
                                                    <CardTitle className="text-base font-bold">{t('contacts.profileInfo', { defaultValue: 'Información del Perfil' })}</CardTitle>
                                                </CardHeader>
                                                <CardContent className="space-y-4 text-xs">
                                                    <div className="grid grid-cols-2 gap-4">
                                                        <div className="space-y-0.5">
                                                            <span className="text-muted-foreground text-[10px]">{t('common.email')}</span>
                                                            <p className="font-semibold text-foreground truncate">{profile.email || '—'}</p>
                                                        </div>
                                                        <div className="space-y-0.5">
                                                            <span className="text-muted-foreground text-[10px]">{t('common.phone')}</span>
                                                            <p className="font-semibold text-foreground">{profile.phone || '—'}</p>
                                                        </div>
                                                        <div className="space-y-0.5">
                                                            <span className="text-muted-foreground text-[10px]">{t('common.city')}</span>
                                                            <p className="font-semibold text-foreground">{(profile as any).city || '—'}</p>
                                                        </div>
                                                        <div className="space-y-0.5">
                                                            <span className="text-muted-foreground text-[10px]">{t('common.country')}</span>
                                                            <p className="font-semibold text-foreground">{(profile as any).country || '—'}</p>
                                                        </div>
                                                        <div className="space-y-0.5">
                                                            <span className="text-muted-foreground text-[10px]">{t('common.source', { defaultValue: 'Origen' })}</span>
                                                            <p className="font-semibold text-foreground capitalize">{(profile as any).source || '—'}</p>
                                                        </div>
                                                        <div className="space-y-0.5">
                                                            <span className="text-muted-foreground text-[10px]">{t('common.leadType', { defaultValue: 'Tipo' })}</span>
                                                            <p className="font-semibold text-foreground capitalize">{String((profile as any).lead_type || '—').replace('_', ' ')}</p>
                                                        </div>
                                                    </div>

                                                    <Separator />

                                                    <div className="flex items-center gap-2">
                                                        <Calendar className="h-4 w-4 text-muted-foreground" />
                                                        <span className="text-muted-foreground">
                                                            Registrado el: <strong className="text-foreground">{formatDateSafe(profile.created_at, 'PPP')}</strong>
                                                        </span>
                                                    </div>
                                                </CardContent>
                                            </Card>
                                        </TabsContent>
                                    </Tabs>
                                </>
                            )}
                        </div>
                    )}
                </div>
            </SheetContent>
        </Sheet>
    );
}
