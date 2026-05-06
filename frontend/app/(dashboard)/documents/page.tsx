'use client';

import { useState, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
    FileText,
    UploadCloud,
    Trash2,
    CheckCircle2,
    Loader2,
    AlertCircle
} from 'lucide-react';
import { toast } from 'sonner';
import { format } from 'date-fns';

import { Button } from '@/components/ui/button';
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from '@/components/ui/card';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import apiClient from '@/lib/api-client';
import type { Document } from '@/types';

import { useTranslation } from 'react-i18next';

export default function DocumentsPage() {
    const { t } = useTranslation();
    const queryClient = useQueryClient();
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [isUploading, setIsUploading] = useState(false);

    // Fetch Documents
    const { data: documents, isLoading } = useQuery({
        queryKey: ['documents'],
        queryFn: async () => {
            const { data } = await apiClient.get<{ data: Document[] }>('/rag');
            return data.data;
        },
    });

    // Upload Mutation
    const uploadMutation = useMutation({
        mutationFn: async (file: File) => {
            const formData = new FormData();
            formData.append('file', file);
            return apiClient.post('/rag/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['documents'] });
            toast.success(t('common.success', { defaultValue: 'Success' }));
            setIsUploading(false);
            if (fileInputRef.current) fileInputRef.current.value = '';
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.error || t('common.error', { defaultValue: 'Error' }));
            setIsUploading(false);
        },
    });

    // Delete Mutation
    const deleteMutation = useMutation({
        mutationFn: async (id: number) => {
            return apiClient.delete(`/rag/${id}`);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['documents'] });
            toast.success(t('common.success', { defaultValue: 'Success' }));
        },
    });

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setIsUploading(true);
            uploadMutation.mutate(e.target.files[0]);
        }
    };

    const formatFileSize = (bytes: number) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">{t('documents.title')}</h2>
                    <p className="text-muted-foreground">
                        {t('documents.description')}
                    </p>
                </div>
            </div>

            <div className="grid gap-6 md:grid-cols-3">
                {/* Upload Card */}
                <Card className="col-span-1 border-dashed bg-muted/30">
                    <CardContent className="flex flex-col items-center justify-center py-10 text-center">
                        <div className="rounded-full bg-background p-4 shadow-sm">
                            <UploadCloud className="h-8 w-8 text-primary" />
                        </div>
                        <h3 className="mt-4 text-lg font-semibold">{t('documents.uploadTitle')}</h3>
                        <p className="mb-4 text-sm text-muted-foreground">
                            {t('documents.uploadDesc')}
                        </p>
                        <Button
                            disabled={isUploading}
                            onClick={() => fileInputRef.current?.click()}
                        >
                            {isUploading ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" /> {t('common.saving', { defaultValue: 'Uploading...' })}
                                </>
                            ) : (
                                t('documents.selectFile')
                            )}
                        </Button>
                        <input
                            type="file"
                            ref={fileInputRef}
                            className="hidden"
                            accept=".pdf,.txt,.md"
                            onChange={handleFileChange}
                        />
                    </CardContent>
                </Card>

                {/* Documents List */}
                <Card className="col-span-2">
                    <CardHeader>
                        <CardTitle>{t('documents.myDocuments')}</CardTitle>
                        <CardDescription>
                            {t('documents.documentsCount', { count: documents?.length || 0 })}
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        {isLoading ? (
                            <div className="space-y-2">
                                <Skeleton className="h-10 w-full" />
                                <Skeleton className="h-10 w-full" />
                                <Skeleton className="h-10 w-full" />
                            </div>
                        ) : documents?.length === 0 ? (
                            <div className="flex flex-col items-center justify-center py-8 text-center text-muted-foreground">
                                <FileText className="mb-2 h-8 w-8 opacity-20" />
                                <p>{t('common.noResults', { defaultValue: 'No documents found.' })}</p>
                            </div>
                        ) : (
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>{t('common.name')}</TableHead>
                                        <TableHead>{t('common.size', { defaultValue: 'Size' })}</TableHead>
                                        <TableHead>{t('common.status')}</TableHead>
                                        <TableHead>{t('common.date', { defaultValue: 'Uploaded' })}</TableHead>
                                        <TableHead className="text-right">{t('common.actions')}</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {documents?.map((doc) => (
                                        <TableRow key={doc.id}>
                                            <TableCell className="font-medium">
                                                <div className="flex items-center gap-2">
                                                    <FileText className="h-4 w-4 text-muted-foreground" />
                                                    {doc.original_filename}
                                                </div>
                                            </TableCell>
                                            <TableCell>{formatFileSize(doc.file_size)}</TableCell>
                                            <TableCell>
                                                {doc.is_processed ? (
                                                    <Badge variant="secondary" className="bg-green-100 text-green-700 hover:bg-green-100">
                                                        <CheckCircle2 className="mr-1 h-3 w-3" /> {t('common.status', { defaultValue: 'Ready' })}
                                                    </Badge>
                                                ) : (
                                                    <Badge variant="secondary" className="bg-yellow-100 text-yellow-700 hover:bg-yellow-100">
                                                        <Loader2 className="mr-1 h-3 w-3 animate-spin" /> {t('common.saving', { defaultValue: 'Processing' })}
                                                    </Badge>
                                                )}
                                            </TableCell>
                                            <TableCell>
                                                {doc.created_at ? format(new Date(doc.created_at), 'MMM d, yyyy') : '-'}
                                            </TableCell>
                                            <TableCell className="text-right">
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    className="h-8 w-8 p-0 text-destructive hover:bg-destructive/10 hover:text-destructive"
                                                    onClick={() => {
                                                        if (confirm(t('common.delete', { defaultValue: 'Delete this document?' }))) deleteMutation.mutate(doc.id);
                                                    }}
                                                >
                                                    <Trash2 className="h-4 w-4" />
                                                </Button>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
