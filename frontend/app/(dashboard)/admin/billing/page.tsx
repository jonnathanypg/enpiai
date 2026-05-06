'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import {
    CreditCard,
    Plus,
    Users,
    Key,
    Loader2,
    ShieldCheck,
    CheckCircle2,
    Package,
    Pencil,
    Trash2,
    X,
    Save,
} from 'lucide-react';
import { toast } from 'sonner';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from '@/components/ui/dialog';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import apiClient from '@/lib/api-client';
import { useAuthStore } from '@/store/use-auth-store';
import type { Plan } from '@/types';

interface AdminDistributor {
    id: number;
    name: string;
    business_name: string | null;
    user_name: string;
    user_email: string;
    is_courtesy: boolean;
    subscription_active: boolean;
    plan_name: string | null;
    created_at: string;
}

export default function AdminBillingPage() {
    const router = useRouter();
    const { t } = useTranslation();
    const queryClient = useQueryClient();
    const user = useAuthStore((s) => s.user);
    const [isPlanDialogOpen, setIsPlanDialogOpen] = useState(false);
    const [isCourtesyDialogOpen, setIsCourtesyDialogOpen] = useState(false);
    const [editingPlanId, setEditingPlanId] = useState<number | null>(null);

    // Guard
    useEffect(() => {
        if (user && user.role !== 'super_admin') {
            router.replace('/dashboard');
        }
    }, [user, router]);

    // Form States
    const [planData, setPlanData] = useState({
        name: '',
        description: '',
        amount: 29.99,
        currency: 'USD',
        frequency_type: 'MONTHLY'
    });

    const [editData, setEditData] = useState<{
        name: string;
        description: string;
        price_monthly: number;
        features: string;
    }>({ name: '', description: '', price_monthly: 0, features: '{}' });

    const [courtesyData, setCourtesyData] = useState({
        name: '',
        email: ''
    });

    // Fetch ALL plans (including inactive for admin)
    const { data: plans, isLoading } = useQuery({
        queryKey: ['admin-plans'],
        queryFn: async () => {
            const { data } = await apiClient.get<Plan[]>('/billing/plans/all');
            return data;
        },
        enabled: user?.role === 'super_admin',
    });

    // Create Plan
    const createPlanMutation = useMutation({
        mutationFn: async (data: typeof planData) => {
            await apiClient.post('/billing/plans', data);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['admin-plans'] });
            toast.success(t('admin.planCreated'));
            setIsPlanDialogOpen(false);
            setPlanData({ name: '', description: '', amount: 29.99, currency: 'USD', frequency_type: 'MONTHLY' });
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.error || t('admin.planCreateError'));
        }
    });

    // Update Plan
    const updatePlanMutation = useMutation({
        mutationFn: async ({ id, data }: { id: number; data: typeof editData }) => {
            let parsedFeatures = null;
            try {
                parsedFeatures = JSON.parse(data.features || '{}');
            } catch(e) {
                throw { response: { data: { error: t('admin.invalidFeaturesJson') } } };
            }
            await apiClient.put(`/billing/plans/${id}`, {
                name: data.name,
                description: data.description,
                amount: data.price_monthly,
                features: parsedFeatures
            });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['admin-plans'] });
            toast.success(t('admin.planUpdated'));
            setEditingPlanId(null);
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.error || t('admin.planUpdateError'));
        }
    });

    // Delete (Deactivate) Plan
    const deletePlanMutation = useMutation({
        mutationFn: async (planId: number) => {
            await apiClient.delete(`/billing/plans/${planId}`);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['admin-plans'] });
            toast.success(t('admin.planDeactivated'));
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.error || t('admin.planDeleteError'));
        }
    });

    // Create Courtesy Account
    const createCourtesyMutation = useMutation({
        mutationFn: async (data: typeof courtesyData) => {
            const { data: response } = await apiClient.post('/billing/courtesy-account', data);
            return response;
        },
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ['admin-distributors'] });
            toast.success(t('admin.courtesyCreated'));
            setIsCourtesyDialogOpen(false);
            setCourtesyData({ name: '', email: '' });
            alert(t('admin.accountCreatedAlert', { email: data.email, password: data.temp_password }));
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.error || t('admin.courtesyCreateError'));
        }
    });

    // Fetch ALL Distributors
    const { data: distributors, isLoading: isLoadingDistributors } = useQuery({
        queryKey: ['admin-distributors'],
        queryFn: async () => {
            const { data } = await apiClient.get<AdminDistributor[]>('/billing/distributors');
            return data;
        },
        enabled: user?.role === 'super_admin',
    });

    // Toggle Courtesy License
    const toggleCourtesyMutation = useMutation({
        mutationFn: async ({ id, is_courtesy }: { id: number, is_courtesy: boolean }) => {
            await apiClient.patch(`/billing/distributors/${id}/courtesy`, { is_courtesy });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['admin-distributors'] });
            toast.success(t('admin.courtesyToggled'));
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.error || t('admin.courtesyToggleError'));
        }
    });
    
    // Delete Distributor
    const deleteDistributorMutation = useMutation({
        mutationFn: async (id: number) => {
            await apiClient.delete(`/admin/tenants/${id}`);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['admin-distributors'] });
            toast.success(t('admin.deleteDistributorSuccess'));
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.error || t('admin.deleteDistributorError'));
        }
    });

    const startEditing = (plan: Plan) => {
        setEditingPlanId(plan.id);
        setEditData({
            name: plan.name,
            description: plan.description || '',
            price_monthly: plan.price_monthly,
            features: plan.features ? JSON.stringify(plan.features, null, 2) : '{\n  "analytics_enabled": false,\n  "channels": "whatsapp",\n  "max_agents": 1,\n  "max_documents": 10,\n  "max_leads": 100,\n  "rag_enabled": true\n}'
        });
    };

    const cancelEditing = () => {
        setEditingPlanId(null);
    };

    const saveEditing = () => {
        if (editingPlanId) {
            updatePlanMutation.mutate({ id: editingPlanId, data: editData });
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
        <div className="mx-auto max-w-6xl space-y-8">
            {/* Header */}
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                    <h2 className="flex items-center gap-2 text-3xl font-bold tracking-tight">
                        <CreditCard className="h-7 w-7 text-primary" />
                        {t('admin.billingTitle')}
                    </h2>
                    <p className="text-muted-foreground">
                        {t('admin.billingDescription')}
                    </p>
                </div>
                <div className="flex gap-2">
                    {/* Courtesy Dialog */}
                    <Dialog open={isCourtesyDialogOpen} onOpenChange={setIsCourtesyDialogOpen}>
                        <DialogTrigger asChild>
                            <Button variant="outline" className="gap-2">
                                <Key className="h-4 w-4" />
                                {t('admin.courtesyAccount')}
                            </Button>
                        </DialogTrigger>
                        <DialogContent>
                            <form onSubmit={(e) => {
                                e.preventDefault();
                                createCourtesyMutation.mutate(courtesyData);
                            }}>
                                <DialogHeader>
                                    <DialogTitle>{t('admin.createCourtesyTitle')}</DialogTitle>
                                    <DialogDescription>
                                        {t('admin.createCourtesyDescription')}
                                    </DialogDescription>
                                </DialogHeader>
                                <div className="grid gap-4 py-4">
                                    <div className="grid gap-2">
                                        <Label htmlFor="c-name">{t('admin.distributorName')}</Label>
                                        <Input 
                                            id="c-name" 
                                            placeholder="John Doe" 
                                            required 
                                            value={courtesyData.name}
                                            onChange={e => setCourtesyData({...courtesyData, name: e.target.value})}
                                        />
                                    </div>
                                    <div className="grid gap-2">
                                        <Label htmlFor="c-email">{t('common.email')}</Label>
                                        <Input 
                                            id="c-email" 
                                            type="email" 
                                            placeholder="john@example.com" 
                                            required 
                                            value={courtesyData.email}
                                            onChange={e => setCourtesyData({...courtesyData, email: e.target.value})}
                                        />
                                    </div>
                                </div>
                                <DialogFooter>
                                    <Button type="submit" disabled={createCourtesyMutation.isPending}>
                                        {createCourtesyMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : t('common.create')}
                                    </Button>
                                </DialogFooter>
                            </form>
                        </DialogContent>
                    </Dialog>

                    {/* New Plan Dialog */}
                    <Dialog open={isPlanDialogOpen} onOpenChange={setIsPlanDialogOpen}>
                        <DialogTrigger asChild>
                            <Button className="gap-2">
                                <Plus className="h-4 w-4" />
                                {t('admin.newPlan')}
                            </Button>
                        </DialogTrigger>
                        <DialogContent>
                            <form onSubmit={(e) => {
                                e.preventDefault();
                                createPlanMutation.mutate(planData);
                            }}>
                                <DialogHeader>
                                    <DialogTitle>{t('admin.createPlanTitle')}</DialogTitle>
                                    <DialogDescription>
                                        {t('admin.createPlanDescription')}
                                    </DialogDescription>
                                </DialogHeader>
                                <div className="grid gap-4 py-4">
                                    <div className="grid gap-2">
                                        <Label htmlFor="p-name">{t('admin.planName')}</Label>
                                        <Input 
                                            id="p-name" 
                                            placeholder={t('admin.planNamePlaceholder')} 
                                            required 
                                            value={planData.name}
                                            onChange={e => setPlanData({...planData, name: e.target.value})}
                                        />
                                    </div>
                                    <div className="grid gap-2">
                                        <Label htmlFor="p-desc">{t('admin.planDescription')}</Label>
                                        <Textarea 
                                            id="p-desc" 
                                            placeholder={t('admin.planDescriptionPlaceholder')} 
                                            value={planData.description}
                                            onChange={e => setPlanData({...planData, description: e.target.value})}
                                        />
                                    </div>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="grid gap-2">
                                            <Label htmlFor="p-amount">{t('admin.monthlyPrice')}</Label>
                                            <Input 
                                                id="p-amount" 
                                                type="number" 
                                                step="0.01" 
                                                required 
                                                value={planData.amount}
                                                onChange={e => setPlanData({...planData, amount: parseFloat(e.target.value)})}
                                            />
                                        </div>
                                        <div className="grid gap-2">
                                            <Label>{t('admin.frequency')}</Label>
                                            <Badge variant="secondary" className="w-fit mt-2">{t('admin.monthly')}</Badge>
                                        </div>
                                    </div>
                                </div>
                                <DialogFooter>
                                    <Button type="submit" disabled={createPlanMutation.isPending}>
                                        {createPlanMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : t('admin.createPlanButton')}
                                    </Button>
                                </DialogFooter>
                            </form>
                        </DialogContent>
                    </Dialog>
                </div>
            </div>

            {/* Plans Table */}
            <Card>
                <CardHeader>
                    <CardTitle className="text-xl flex items-center gap-2">
                        <Package className="h-5 w-5" />
                        {t('admin.plansTitle')}
                    </CardTitle>
                    <CardDescription>
                        {t('admin.plansDescription')}
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {isLoading ? (
                        <div className="flex justify-center py-8">
                            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                        </div>
                    ) : !plans?.length ? (
                        <div className="text-center py-12 text-muted-foreground">
                            {t('admin.noPlans')}
                        </div>
                    ) : (
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>{t('common.name')}</TableHead>
                                    <TableHead>{t('common.description')}</TableHead>
                                    <TableHead>{t('common.price')}</TableHead>
                                    <TableHead>{t('admin.dLocalToken')}</TableHead>
                                    <TableHead>{t('common.status')}</TableHead>
                                    <TableHead className="text-right">{t('common.actions')}</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {plans.map((plan) => (
                                    <TableRow key={plan.id}>
                                        <TableCell className="font-medium">
                                            {editingPlanId === plan.id ? (
                                                <Input
                                                    value={editData.name}
                                                    onChange={(e) => setEditData({ ...editData, name: e.target.value })}
                                                    className="h-8 w-40"
                                                />
                                            ) : t(`planNames.${plan.name}`, plan.name)}
                                        </TableCell>
                                        <TableCell className="max-w-[300px]">
                                            {editingPlanId === plan.id ? (
                                                <div className="flex flex-col gap-2">
                                                    <Input
                                                        value={editData.description}
                                                        onChange={(e) => setEditData({ ...editData, description: e.target.value })}
                                                        className="h-8"
                                                        placeholder={t('admin.shortDescription')}
                                                    />
                                                    <Textarea
                                                        value={editData.features}
                                                        onChange={(e) => setEditData({ ...editData, features: e.target.value })}
                                                        className="min-h-[140px] font-mono text-[10px]"
                                                        placeholder='{"rag_enabled": true}'
                                                    />
                                                </div>
                                            ) : (
                                                <div className="flex flex-col gap-1">
                                                    <span className="truncate block">
                                                        {t(`planDescriptions.${plan.name}`, plan.description || '—')}
                                                    </span>
                                                    {plan.features && (
                                                        <div className="flex flex-wrap gap-1 mt-1">
                                                            {Object.entries(plan.features as any).map(([k, v]) => (
                                                                <Badge key={k} variant="outline" className="text-[10px] py-0 h-5 px-1.5 font-normal">
                                                                    {t(`planFeatures.${k.replace(/ /g, '_')}`, k.replace(/_/g, ' '))}: {
                                                                        typeof v === 'boolean' ? t(`planFeatures.${v}`) : String(v)
                                                                    }
                                                                </Badge>
                                                            ))}
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                        </TableCell>
                                        <TableCell>
                                            {editingPlanId === plan.id ? (
                                                <Input
                                                    type="number"
                                                    step="0.01"
                                                    value={editData.price_monthly}
                                                    onChange={(e) => setEditData({ ...editData, price_monthly: parseFloat(e.target.value) })}
                                                    className="h-8 w-24"
                                                />
                                            ) : `$${plan.price_monthly}${t('common.perMonth')}`}
                                        </TableCell>
                                        <TableCell className="font-mono text-xs opacity-60">
                                            {plan.dlocal_plan_token
                                                ? `${plan.dlocal_plan_token.substring(0, 12)}...`
                                                : <span className="text-yellow-600">{t('admin.local')}</span>
                                            }
                                        </TableCell>
                                        <TableCell>
                                            <Badge variant={plan.is_active ? "default" : "secondary"}>
                                                {plan.is_active ? t('common.active') : t('common.inactive')}
                                            </Badge>
                                        </TableCell>
                                        <TableCell className="text-right">
                                            {editingPlanId === plan.id ? (
                                                <div className="flex justify-end gap-1">
                                                    <Button
                                                        size="icon"
                                                        variant="ghost"
                                                        onClick={saveEditing}
                                                        disabled={updatePlanMutation.isPending}
                                                        className="h-8 w-8 text-green-600"
                                                    >
                                                        {updatePlanMutation.isPending
                                                            ? <Loader2 className="h-4 w-4 animate-spin" />
                                                            : <Save className="h-4 w-4" />
                                                        }
                                                    </Button>
                                                    <Button
                                                        size="icon"
                                                        variant="ghost"
                                                        onClick={cancelEditing}
                                                        className="h-8 w-8"
                                                    >
                                                        <X className="h-4 w-4" />
                                                    </Button>
                                                </div>
                                            ) : (
                                                <div className="flex justify-end gap-1">
                                                    <Button
                                                        size="icon"
                                                        variant="ghost"
                                                        onClick={() => startEditing(plan)}
                                                        className="h-8 w-8"
                                                    >
                                                        <Pencil className="h-4 w-4" />
                                                    </Button>
                                                    {plan.is_active && (
                                                        <Button
                                                            size="icon"
                                                            variant="ghost"
                                                            className="h-8 w-8 text-destructive hover:text-destructive"
                                                            onClick={() => {
                                                                if (confirm(t('admin.deactivatePlanConfirm', { name: plan.name }))) {
                                                                    deletePlanMutation.mutate(plan.id);
                                                                }
                                                            }}
                                                            disabled={deletePlanMutation.isPending}
                                                        >
                                                            <Trash2 className="h-4 w-4" />
                                                        </Button>
                                                    )}
                                                </div>
                                            )}
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    )}
                </CardContent>
            </Card>

            {/* Distributors Table */}
            <Card>
                <CardHeader>
                    <CardTitle className="text-xl flex items-center gap-2">
                        <Users className="h-5 w-5" />
                        {t('admin.distributorsTitle')}
                    </CardTitle>
                    <CardDescription>
                        {t('admin.distributorsDescription')}
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {isLoadingDistributors ? (
                        <div className="flex justify-center py-8">
                            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                        </div>
                    ) : !distributors?.length ? (
                        <div className="text-center py-12 text-muted-foreground">
                            {t('admin.noDistributors')}
                        </div>
                    ) : (
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>{t('admin.distributor')}</TableHead>
                                    <TableHead>{t('common.email')}</TableHead>
                                    <TableHead>{t('admin.currentPlan')}</TableHead>
                                    <TableHead>{t('admin.subscription')}</TableHead>
                                    <TableHead className="text-right">{t('admin.courtesyLicense')}</TableHead>
                                    <TableHead className="text-right">{t('common.actions')}</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {distributors.map((dist) => (
                                    <TableRow key={dist.id}>
                                        <TableCell>
                                            <div className="font-medium">{dist.name}</div>
                                            <div className="text-xs text-muted-foreground">
                                                {t('admin.registered')}: {new Date(dist.created_at).toLocaleDateString()}
                                            </div>
                                        </TableCell>
                                        <TableCell>{dist.user_email || '—'}</TableCell>
                                        <TableCell>
                                            {dist.plan_name ? (
                                                <Badge variant="outline">{dist.plan_name}</Badge>
                                            ) : (
                                                <span className="text-muted-foreground">—</span>
                                            )}
                                        </TableCell>
                                        <TableCell>
                                            {dist.subscription_active ? (
                                                <Badge className="bg-green-500 tracking-wide text-[10px] uppercase">{t('common.active')}</Badge>
                                            ) : (
                                                <Badge variant="secondary" className="tracking-wide text-[10px] uppercase">{t('common.inactive')}</Badge>
                                            )}
                                        </TableCell>
                                        <TableCell className="text-right">
                                            <div className="flex items-center justify-end gap-2">
                                                <Switch 
                                                    checked={dist.is_courtesy}
                                                    onCheckedChange={(checked) => {
                                                        toggleCourtesyMutation.mutate({ 
                                                            id: dist.id, 
                                                            is_courtesy: checked 
                                                        });
                                                    }}
                                                    disabled={toggleCourtesyMutation.isPending}
                                                />
                                                <Button
                                                    size="icon"
                                                    variant="ghost"
                                                    className="h-8 w-8 text-destructive hover:text-destructive hover:bg-destructive/10"
                                                    onClick={() => {
                                                        if (confirm(t('admin.deleteDistributorConfirm', { name: dist.name }))) {
                                                            deleteDistributorMutation.mutate(dist.id);
                                                        }
                                                    }}
                                                    disabled={deleteDistributorMutation.isPending}
                                                >
                                                    {deleteDistributorMutation.isPending && deleteDistributorMutation.variables === dist.id ? (
                                                        <Loader2 className="h-4 w-4 animate-spin" />
                                                    ) : (
                                                        <Trash2 className="h-4 w-4" />
                                                    )}
                                                </Button>
                                            </div>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    )}
                </CardContent>
            </Card>

            {/* Info Cards */}
            <div className="grid gap-6 md:grid-cols-2">
                <Card className="bg-green-500/5 border-green-500/10">
                    <CardHeader>
                        <CardTitle className="text-sm flex items-center gap-2 text-green-700">
                            <ShieldCheck className="h-4 w-4" />
                            {t('admin.integrationStatus')}
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="flex items-center gap-2">
                            <CheckCircle2 className="h-5 w-5 text-green-500" />
                            <span className="font-medium">{t('admin.dLocalConfigured')}</span>
                        </div>
                        <p className="text-xs text-muted-foreground mt-2">
                            {t('admin.integrationNote')}
                        </p>
                    </CardContent>
                </Card>

                <Card className="bg-blue-500/5 border-blue-500/10">
                    <CardHeader>
                        <CardTitle className="text-sm flex items-center gap-2 text-blue-700">
                            <Users className="h-4 w-4" />
                            {t('admin.courtesyTitle')}
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-sm">
                            {t('admin.courtesyNote')}
                        </p>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
