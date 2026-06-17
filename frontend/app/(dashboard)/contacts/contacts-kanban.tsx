'use client';

import React, { useState, useEffect } from 'react';
import { DragDropContext, Droppable, Draggable, DropResult } from '@hello-pangea/dnd';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/lib/api-client';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { toast } from 'sonner';
import { useTranslation } from 'react-i18next';
import { Mail, Phone, Award } from 'lucide-react';
import type { Lead } from '@/types';

interface ContactsKanbanProps {
    search: string;
    onContactClick: (id: number) => void;
}

const COLUMNS = [
    { id: 'new', nameKey: 'contacts.status.new', defaultName: 'Nuevo' },
    { id: 'contacted', nameKey: 'contacts.status.contacted', defaultName: 'Contactado' },
    { id: 'qualified', nameKey: 'contacts.status.qualified', defaultName: 'Calificado' },
    { id: 'nurturing', nameKey: 'contacts.status.nurturing', defaultName: 'En Seguimiento' },
    { id: 'converted', nameKey: 'contacts.status.converted', defaultName: 'Convertido' },
    { id: 'lost', nameKey: 'contacts.status.lost', defaultName: 'Perdido' }
];

export default function ContactsKanban({ search, onContactClick }: ContactsKanbanProps) {
    const { t } = useTranslation();
    const queryClient = useQueryClient();

    // 1. Fetch Leads
    const { data: leads, isLoading: loadingLeads } = useQuery<Lead[]>({
        queryKey: ['contacts-kanban', search],
        queryFn: async () => {
            const params = search ? `?search=${encodeURIComponent(search)}` : '';
            // Fetch all leads without pagination (or high page size) to populate Kanban boards
            const { data } = await apiClient.get<{ data: Lead[] }>(`/leads${params}`);
            return data.data;
        }
    });

    // 2. Qualify / Move Lead Mutation
    const moveLeadMutation = useMutation({
        mutationFn: async ({ leadId, status }: { leadId: number; status: string }) => {
            return apiClient.post(`/leads/${leadId}/qualify`, { status });
        },
        onMutate: async (variables) => {
            await queryClient.cancelQueries({ queryKey: ['contacts-kanban', search] });
            const previousLeads = queryClient.getQueryData<Lead[]>(['contacts-kanban', search]);
            
            if (previousLeads) {
                queryClient.setQueryData<Lead[]>(
                    ['contacts-kanban', search],
                    previousLeads.map(l => l.id === variables.leadId ? { ...l, status: variables.status as any } : l)
                );
            }
            return { previousLeads };
        },
        onError: (err, variables, context) => {
            if (context?.previousLeads) {
                queryClient.setQueryData(['contacts-kanban', search], context.previousLeads);
            }
            toast.error(t('common.error', { defaultValue: 'Failed to move contact' }));
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['contacts-kanban', search] });
            queryClient.invalidateQueries({ queryKey: ['contacts'] });
        }
    });

    const handleDragEnd = (result: DropResult) => {
        const { source, destination, draggableId } = result;
        if (!destination) return;

        const sourceStatus = source.droppableId;
        const destStatus = destination.droppableId;

        if (sourceStatus === destStatus) return;

        const leadId = parseInt(draggableId);
        moveLeadMutation.mutate({ leadId, status: destStatus });
    };

    if (loadingLeads) {
        return (
            <div className="flex gap-4 p-2 overflow-x-auto">
                {Array.from({ length: 4 }).map((_, i) => (
                    <div key={i} className="w-80 flex-shrink-0 space-y-4">
                        <Skeleton className="h-8 w-1/2 rounded" />
                        <Skeleton className="h-32 w-full rounded-xl" />
                        <Skeleton className="h-32 w-full rounded-xl" />
                    </div>
                ))}
            </div>
        );
    }

    return (
        <DragDropContext onDragEnd={handleDragEnd}>
            <div className="flex gap-4 overflow-x-auto pb-4 select-none min-h-[500px]">
                {COLUMNS.map(column => {
                    const columnLeads = (leads || []).filter(l => (l.status || 'new') === column.id);
                    return (
                        <div key={column.id} className="w-80 flex-shrink-0 bg-muted/30 rounded-xl p-3 border flex flex-col max-h-[75vh]">
                            <div className="flex justify-between items-center mb-3 px-1">
                                <h3 className="font-semibold text-sm text-foreground flex items-center gap-2">
                                    {t(column.nameKey, { defaultValue: column.defaultName })}
                                    <Badge variant="secondary" className="text-[10px] py-0.5 px-1.5">{columnLeads.length}</Badge>
                                </h3>
                            </div>

                            <Droppable droppableId={column.id}>
                                {(provided, snapshot) => (
                                    <div
                                        ref={provided.innerRef}
                                        {...provided.droppableProps}
                                        className={`flex-1 overflow-y-auto space-y-2.5 min-h-[300px] rounded-lg transition-colors p-1 ${
                                            snapshot.isDraggingOver ? 'bg-accent/40' : ''
                                        }`}
                                    >
                                        {columnLeads.map((lead, index) => (
                                            <DraggableCard key={lead.id} lead={lead} index={index} t={t} onContactClick={onContactClick} />
                                        ))}
                                        {provided.placeholder}
                                    </div>
                                )}
                            </Droppable>
                        </div>
                    );
                })}
            </div>
        </DragDropContext>
    );
}

function DraggableCard({ lead, index, t, onContactClick }: { lead: Lead; index: number; t: any; onContactClick: (id: number) => void }) {
    const fullName = `${lead.first_name || ''} ${lead.last_name || ''}`.trim() || lead.phone || t('common.unknown', { defaultValue: 'Desconocido' });
    const rawScore = lead.score ?? lead.metadata?.score ?? 0;
    const score = Number(rawScore) || 0;
    
    return (
        <Draggable draggableId={lead.id.toString()} index={index}>
            {(provided, snapshot) => (
                <div
                    ref={provided.innerRef}
                    {...provided.draggableProps}
                    {...provided.dragHandleProps}
                    className={`block hover:shadow-md transition-shadow duration-200 border-l-4 rounded-lg bg-card text-card-foreground shadow-sm ${
                        score >= 80 ? 'border-l-emerald-500' : score >= 50 ? 'border-l-amber-500' : 'border-l-slate-300'
                    } ${snapshot.isDragging ? 'rotate-1 scale-102 shadow-lg ring-1 ring-primary/10' : ''}`}
                >
                    <Card className="border-0 shadow-none bg-transparent">
                        <CardContent className="p-3.5 space-y-2.5">
                            <div className="flex justify-between items-start gap-2">
                                <button 
                                    onClick={() => onContactClick(lead.id)}
                                    className="font-semibold text-xs text-foreground hover:underline text-left line-clamp-1"
                                >
                                    {fullName}
                                </button>
                                <Badge 
                                    variant={score >= 80 ? 'default' : 'secondary'}
                                    className={`text-[9px] font-bold py-0.5 px-1 ${
                                        score >= 80 ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 hover:bg-emerald-200 border-0' : ''
                                    }`}
                                >
                                    {score}
                                </Badge>
                            </div>

                            <div className="space-y-1 text-[10px] text-muted-foreground">
                                {lead.email && <div className="flex items-center gap-1.5 truncate"><Mail className="h-3 w-3 flex-shrink-0" /> {lead.email}</div>}
                                {lead.phone && <div className="flex items-center gap-1.5"><Phone className="h-3 w-3 flex-shrink-0" /> {lead.phone}</div>}
                            </div>
                        </CardContent>
                    </Card>
                </div>
            )}
        </Draggable>
    );
}
