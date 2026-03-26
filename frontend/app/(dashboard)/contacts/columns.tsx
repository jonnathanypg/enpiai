'use client';

import { ColumnDef } from '@tanstack/react-table';
import { MoreHorizontal, ArrowUpDown, Phone, Mail, MessageSquare, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import Link from 'next/link';
import type { Lead } from '@/types';
import { TFunction } from 'i18next';

export const getColumns = (t: TFunction, onDelete?: (lead: Lead) => void): ColumnDef<Lead>[] => [
    {
        accessorKey: 'name',
        header: t('common.name'),
        cell: ({ row }) => {
            const lead = row.original;
            let fullName = `${lead.first_name || ''} ${lead.last_name || ''}`.trim();
            if (!fullName) {
                fullName = lead.phone || 'Desconocido';
            }
            return (
                <div className="flex flex-col">
                    <Link href={`/contacts/lead:${lead.id}`} className="font-medium hover:underline">
                        {fullName}
                    </Link>
                    <span className="text-xs text-muted-foreground">{lead.email}</span>
                </div>
            );
        },
    },
    {
        accessorKey: 'status',
        header: t('common.status'),
        cell: ({ row }) => {
            const status = row.getValue('status') as string;
            const variant =
                status === 'qualified'
                    ? 'default'
                    : status === 'converted'
                        ? 'outline'
                        : 'secondary';

            return <Badge variant={variant} className="capitalize">{status}</Badge>;
        },
    },
    {
        accessorKey: 'score',
        header: ({ column }) => {
            return (
                <Button
                    variant="ghost"
                    onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
                >
                    Score
                    <ArrowUpDown className="ml-2 h-4 w-4" />
                </Button>
            );
        },
        cell: ({ row }) => {
            const rawScore = row.getValue('score') ?? row.original.metadata?.score ?? 0;
            const score = parseFloat(rawScore as string) || 0;
            const color = score > 80 ? 'text-green-600' : score > 50 ? 'text-yellow-600' : 'text-red-600';
            return <div className={`font-bold ${color}`}>{score}</div>;
        },
    },
    {
        accessorKey: 'source',
        header: t('admin.distributor'),
        cell: ({ row }) => <div className="capitalize">{row.getValue('source')}</div>,
    },
    {
        id: 'actions',
        cell: ({ row }) => {
            const lead = row.original;

            return (
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button variant="ghost" className="h-8 w-8 p-0">
                            <span className="sr-only">{t('common.actions')}</span>
                            <MoreHorizontal className="h-4 w-4" />
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                        <DropdownMenuLabel>{t('common.actions')}</DropdownMenuLabel>
                        <DropdownMenuItem onClick={() => navigator.clipboard.writeText(lead.phone || '')}>
                            <Phone className="mr-2 h-4 w-4" /> {t('common.save')} Phone
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <Link href={`/contacts/${lead.id}`}>
                            <DropdownMenuItem>{t('distributorDashboard.viewContacts')}</DropdownMenuItem>
                        </Link>
                        <DropdownMenuItem
                            className="text-destructive focus:text-destructive"
                            onClick={() => onDelete?.(lead)}
                        >
                            <Trash2 className="mr-2 h-4 w-4" /> {t('common.delete', { defaultValue: 'Eliminar' })}
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
            );
        },
    },
];

