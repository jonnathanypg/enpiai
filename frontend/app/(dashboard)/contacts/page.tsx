'use client';

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { List, LayoutGrid, Search } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import ContactsTable from './contacts-table';
import ContactsKanban from './contacts-kanban';
import ContactDetailsDrawer from './contact-details-drawer';
import { useQueryClient } from '@tanstack/react-query';

export default function ContactsPage() {
    const { t } = useTranslation();
    const queryClient = useQueryClient();
    const [viewMode, setViewMode] = useState<'table' | 'kanban'>('kanban');
    const [search, setSearch] = useState('');
    const [selectedContactId, setSelectedContactId] = useState<number | null>(null);

    const handleContactClick = (id: number) => {
        setSelectedContactId(id);
    };

    const handleUpdate = () => {
        queryClient.invalidateQueries({ queryKey: ['contacts'] });
        queryClient.invalidateQueries({ queryKey: ['contacts-kanban'] });
    };

    return (
        <div className="space-y-6 pb-12">
            {/* Header section with view toggle */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">{t('contacts.title', { defaultValue: 'Contactos' })}</h2>
                    <p className="text-sm text-muted-foreground mt-1">
                        {t('contacts.subtitle', { defaultValue: 'Gestiona, organiza y prioriza tu flujo de prospectos en tiempo real.' })}
                    </p>
                </div>
                
                <Tabs 
                    value={viewMode} 
                    onValueChange={(val) => setViewMode(val as 'table' | 'kanban')} 
                    className="w-auto"
                >
                    <TabsList className="grid grid-cols-2 w-[220px]">
                        <TabsTrigger value="table" className="gap-1.5 text-xs">
                            <List className="h-3.5 w-3.5" />
                            {t('contacts.viewTable', { defaultValue: 'Lista' })}
                        </TabsTrigger>
                        <TabsTrigger value="kanban" className="gap-1.5 text-xs">
                            <LayoutGrid className="h-3.5 w-3.5" />
                            {t('contacts.viewKanban', { defaultValue: 'Kanban' })}
                        </TabsTrigger>
                    </TabsList>
                </Tabs>
            </div>

            {/* Global search and filter block */}
            <div className="flex items-center gap-2 p-3 bg-muted/20 rounded-xl border">
                <div className="relative flex-1 max-w-sm">
                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                        placeholder={t('contacts.filterPlaceholder', { defaultValue: 'Filtrar nombres...' })}
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="pl-9 bg-background"
                    />
                </div>
            </div>

            {/* Dynamic Rendering */}
            <div className="mt-4">
                {viewMode === 'table' ? (
                    <ContactsTable search={search} onContactClick={handleContactClick} />
                ) : (
                    <ContactsKanban search={search} onContactClick={handleContactClick} />
                )}
            </div>

            {/* In-page Slide-out Details Drawer */}
            <ContactDetailsDrawer
                contactId={selectedContactId}
                isOpen={selectedContactId !== null}
                onClose={() => setSelectedContactId(null)}
                onUpdate={handleUpdate}
            />
        </div>
    );
}
