'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import {
    FileText,
    Upload,
    Trash2,
    Loader2,
    Globe,
    File,
} from 'lucide-react';
import { toast } from 'sonner';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import apiClient from '@/lib/api-client';
import { useAuthStore } from '@/store/use-auth-store';

interface RAGDocument {
    id: number;
    filename: string;
    original_filename: string;
    file_type: string;
    file_size: number;
    chunk_count: number;
    is_processed: boolean;
    description: string | null;
    tags: string[];
    created_at: string;
    processed_at: string | null;
}

function formatFileSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function AdminDocumentsPage() {
    const router = useRouter();
    const { t } = useTranslation();
    const queryClient = useQueryClient();
    const user = useAuthStore((s) => s.user);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [isUploading, setIsUploading] = useState(false);

    // Guard: Super Admin only
    useEffect(() => {
        if (user && user.role !== 'super_admin') {
            router.replace('/dashboard');
        }
    }, [user, router]);

    // Fetch global documents
    const { data: documents, isLoading } = useQuery({
        queryKey: ['admin-documents'],
        queryFn: async () => {
            const { data } = await apiClient.get<{ data: RAGDocument[] }>('/rag');
            return data.data;
        },
        enabled: user?.role === 'super_admin',
    });

    // Delete mutation
    const deleteMutation = useMutation({
        mutationFn: async (docId: number) => {
            await apiClient.delete(`/rag/${docId}`);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['admin-documents'] });
            toast.success(t('adminDocuments.documentDeleted'));
        },
        onError: () => {
            toast.error(t('adminDocuments.deleteError'));
        },
    });

    // Upload handler
    const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setIsUploading(true);
        try {
            const formData = new FormData();
            formData.append('file', file);

            await apiClient.post('/rag/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });

            queryClient.invalidateQueries({ queryKey: ['admin-documents'] });
            toast.success(t('adminDocuments.uploadSuccess', { name: file.name }));
        } catch (error: unknown) {
            const message =
                (error as { response?: { data?: { error?: string } } })?.response?.data?.error ||
                t('adminDocuments.uploadError');
            toast.error(message);
        } finally {
            setIsUploading(false);
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    if (user?.role !== 'super_admin') {
        return (
            <div className="flex h-[50vh] items-center justify-center">
                <p className="text-lg text-muted-foreground">{t('common.accessDenied')}</p>
            </div>
        );
    }

    return (
        <div className="mx-auto max-w-4xl space-y-8">
            {/* Header */}
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                    <h2 className="flex items-center gap-2 text-3xl font-bold tracking-tight">
                        <Globe className="h-7 w-7 text-primary" />
                        {t('adminDocuments.title')}
                    </h2>
                    <p className="text-muted-foreground">
                        {t('adminDocuments.description')}
                    </p>
                </div>
                <div>
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept=".pdf,.txt,.md"
                        className="hidden"
                        onChange={handleUpload}
                    />
                    <Button
                        onClick={() => fileInputRef.current?.click()}
                        disabled={isUploading}
                        className="gap-2"
                    >
                        {isUploading ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                            <Upload className="h-4 w-4" />
                        )}
                        {isUploading ? t('adminDocuments.uploading') : t('adminDocuments.uploadButton')}
                    </Button>
                </div>
            </div>

            <Separator />

            {/* Info Alert */}
            <Alert className="bg-blue-500/10 border-blue-500/20">
                <Globe className="h-4 w-4 text-blue-600" />
                <AlertDescription className="text-blue-700 dark:text-blue-300">
                    {t('adminDocuments.knowledgeBaseNote')}
                    {' '}
                    {t('adminDocuments.supportedFormats')}
                </AlertDescription>
            </Alert>

            {/* Documents List */}
            {isLoading ? (
                <div className="space-y-4">
                    <Skeleton className="h-20 w-full" />
                    <Skeleton className="h-20 w-full" />
                    <Skeleton className="h-20 w-full" />
                </div>
            ) : !documents?.length ? (
                <Card>
                    <CardContent className="flex flex-col items-center justify-center py-16 text-center">
                        <FileText className="h-12 w-12 text-muted-foreground/40 mb-4" />
                        <p className="text-lg font-medium text-muted-foreground">
                            {t('adminDocuments.noDocuments')}
                        </p>
                        <p className="text-sm text-muted-foreground/70 mt-1">
                            {t('adminDocuments.noDocumentsNote')}
                        </p>
                    </CardContent>
                </Card>
            ) : (
                <div className="space-y-3">
                    {documents.map((doc) => (
                        <Card key={doc.id} className="transition-shadow hover:shadow-md">
                            <CardContent className="flex items-center justify-between py-4">
                                <div className="flex items-center gap-4 min-w-0">
                                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                                        <File className="h-5 w-5 text-primary" />
                                    </div>
                                    <div className="min-w-0">
                                        <p className="font-medium truncate">
                                            {doc.original_filename}
                                        </p>
                                        <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground mt-1">
                                            <span>{formatFileSize(doc.file_size)}</span>
                                            <span>·</span>
                                            <span>{doc.chunk_count} {t('adminDocuments.chunks')}</span>
                                            <span>·</span>
                                            <span>
                                                {new Date(doc.created_at).toLocaleDateString()}
                                            </span>
                                            <Badge
                                                variant="outline"
                                                className={
                                                    doc.is_processed
                                                        ? 'border-green-500 text-green-600'
                                                        : 'border-yellow-500 text-yellow-600'
                                                }
                                            >
                                                {doc.is_processed ? t('adminDocuments.indexed') : t('adminDocuments.processing')}
                                            </Badge>
                                        </div>
                                    </div>
                                </div>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="text-destructive hover:text-destructive shrink-0"
                                    onClick={() => {
                                        if (confirm(t('adminDocuments.deleteConfirm', { name: doc.original_filename }))) {
                                            deleteMutation.mutate(doc.id);
                                        }
                                    }}
                                    disabled={deleteMutation.isPending}
                                >
                                    <Trash2 className="h-4 w-4" />
                                </Button>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    );
}
