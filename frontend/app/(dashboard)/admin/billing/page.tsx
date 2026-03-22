'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
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
            toast.success('Plan creado exitosamente.');
            setIsPlanDialogOpen(false);
            setPlanData({ name: '', description: '', amount: 29.99, currency: 'USD', frequency_type: 'MONTHLY' });
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.error || 'Error al crear el plan.');
        }
    });

    // Update Plan
    const updatePlanMutation = useMutation({
        mutationFn: async ({ id, data }: { id: number; data: typeof editData }) => {
            let parsedFeatures = null;
            try {
                parsedFeatures = JSON.parse(data.features || '{}');
            } catch(e) {
                throw { response: { data: { error: 'Formato JSON inválido en las características (features)' } } };
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
            toast.success('Plan actualizado.');
            setEditingPlanId(null);
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.error || 'Error al actualizar.');
        }
    });

    // Delete (Deactivate) Plan
    const deletePlanMutation = useMutation({
        mutationFn: async (planId: number) => {
            await apiClient.delete(`/billing/plans/${planId}`);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['admin-plans'] });
            toast.success('Plan desactivado.');
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.error || 'Error al eliminar.');
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
            toast.success('Cuenta de cortesía creada.');
            setIsCourtesyDialogOpen(false);
            setCourtesyData({ name: '', email: '' });
            alert(`Cuenta Creada!\nEmail: ${data.email}\nPassword Temporal: ${data.temp_password}\n\nPor favor copia estos datos ahora.`);
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.error || 'Error al crear la cuenta.');
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
            toast.success('Estado de cortesía actualizado.');
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.error || 'Error al actualizar cortesía.');
        }
    });

    const startEditing = (plan: Plan) => {
        setEditingPlanId(plan.id);
        setEditData({
            name: plan.name,
            description: plan.description || '',
            price_monthly: plan.price_monthly,
            features: plan.features ? JSON.stringify(plan.features, null, 2) : '{\n  "analytics enabled": false,\n  "channels": "whatsapp",\n  "max agents": 1,\n  "max documents": 10,\n  "max leads": 100,\n  "rag enabled": true\n}'
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
                <p className="text-lg text-muted-foreground">Acceso denegado.</p>
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
                        Facturación y Licencias
                    </h2>
                    <p className="text-muted-foreground">
                        Gestiona los planes de suscripción, la integración con dLocal Go y las cuentas de cortesía.
                    </p>
                </div>
                <div className="flex gap-2">
                    {/* Courtesy Dialog */}
                    <Dialog open={isCourtesyDialogOpen} onOpenChange={setIsCourtesyDialogOpen}>
                        <DialogTrigger asChild>
                            <Button variant="outline" className="gap-2">
                                <Key className="h-4 w-4" />
                                Cuenta de Cortesía
                            </Button>
                        </DialogTrigger>
                        <DialogContent>
                            <form onSubmit={(e) => {
                                e.preventDefault();
                                createCourtesyMutation.mutate(courtesyData);
                            }}>
                                <DialogHeader>
                                    <DialogTitle>Crear Cuenta de Cortesía</DialogTitle>
                                    <DialogDescription>
                                        Crea un nuevo distribuidor que podrá usar la plataforma sin pasar por la pasarela de pago.
                                        Se generará una contraseña temporal.
                                    </DialogDescription>
                                </DialogHeader>
                                <div className="grid gap-4 py-4">
                                    <div className="grid gap-2">
                                        <Label htmlFor="c-name">Nombre del Distribuidor</Label>
                                        <Input 
                                            id="c-name" 
                                            placeholder="Juan Pérez" 
                                            required 
                                            value={courtesyData.name}
                                            onChange={e => setCourtesyData({...courtesyData, name: e.target.value})}
                                        />
                                    </div>
                                    <div className="grid gap-2">
                                        <Label htmlFor="c-email">Correo Electrónico</Label>
                                        <Input 
                                            id="c-email" 
                                            type="email" 
                                            placeholder="juan@ejemplo.com" 
                                            required 
                                            value={courtesyData.email}
                                            onChange={e => setCourtesyData({...courtesyData, email: e.target.value})}
                                        />
                                    </div>
                                </div>
                                <DialogFooter>
                                    <Button type="submit" disabled={createCourtesyMutation.isPending}>
                                        {createCourtesyMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Crear Cuenta'}
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
                                Nuevo Plan
                            </Button>
                        </DialogTrigger>
                        <DialogContent>
                            <form onSubmit={(e) => {
                                e.preventDefault();
                                createPlanMutation.mutate(planData);
                            }}>
                                <DialogHeader>
                                    <DialogTitle>Crear Plan de Suscripción</DialogTitle>
                                    <DialogDescription>
                                        Se intentará sincronizar el plan con dLocal Go automáticamente.
                                        Si las credenciales no están configuradas, el plan se guardará localmente.
                                    </DialogDescription>
                                </DialogHeader>
                                <div className="grid gap-4 py-4">
                                    <div className="grid gap-2">
                                        <Label htmlFor="p-name">Nombre del Plan</Label>
                                        <Input 
                                            id="p-name" 
                                            placeholder="Licencia Personal" 
                                            required 
                                            value={planData.name}
                                            onChange={e => setPlanData({...planData, name: e.target.value})}
                                        />
                                    </div>
                                    <div className="grid gap-2">
                                        <Label htmlFor="p-desc">Descripción</Label>
                                        <Textarea 
                                            id="p-desc" 
                                            placeholder="Acceso completo para 1 distribuidor..." 
                                            value={planData.description}
                                            onChange={e => setPlanData({...planData, description: e.target.value})}
                                        />
                                    </div>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="grid gap-2">
                                            <Label htmlFor="p-amount">Precio Mensual (USD)</Label>
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
                                            <Label>Frecuencia</Label>
                                            <Badge variant="secondary" className="w-fit mt-2">MENSUAL</Badge>
                                        </div>
                                    </div>
                                </div>
                                <DialogFooter>
                                    <Button type="submit" disabled={createPlanMutation.isPending}>
                                        {createPlanMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Crear Plan'}
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
                        Planes de Suscripción
                    </CardTitle>
                    <CardDescription>
                        Todos los planes disponibles. Los inactivos no se mostrarán a los distribuidores.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {isLoading ? (
                        <div className="flex justify-center py-8">
                            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                        </div>
                    ) : !plans?.length ? (
                        <div className="text-center py-12 text-muted-foreground">
                            No hay planes creados aún. Haz clic en &quot;Nuevo Plan&quot; para comenzar.
                        </div>
                    ) : (
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Nombre</TableHead>
                                    <TableHead>Descripción</TableHead>
                                    <TableHead>Precio</TableHead>
                                    <TableHead>dLocal Token</TableHead>
                                    <TableHead>Estado</TableHead>
                                    <TableHead className="text-right">Acciones</TableHead>
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
                                            ) : plan.name}
                                        </TableCell>
                                        <TableCell className="max-w-[300px]">
                                            {editingPlanId === plan.id ? (
                                                <div className="flex flex-col gap-2">
                                                    <Input
                                                        value={editData.description}
                                                        onChange={(e) => setEditData({ ...editData, description: e.target.value })}
                                                        className="h-8"
                                                        placeholder="Descripción breve..."
                                                    />
                                                    <Textarea
                                                        value={editData.features}
                                                        onChange={(e) => setEditData({ ...editData, features: e.target.value })}
                                                        className="min-h-[140px] font-mono text-[10px]"
                                                        placeholder='{"rag enabled": true}'
                                                    />
                                                </div>
                                            ) : (
                                                <div className="flex flex-col gap-1">
                                                    <span className="truncate block">{plan.description || '—'}</span>
                                                    {plan.features && (
                                                        <pre className="text-[10px] text-muted-foreground bg-secondary/30 p-2 rounded mt-1 overflow-x-auto max-w-[280px]">
                                                            {JSON.stringify(plan.features, null, 2)}
                                                        </pre>
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
                                            ) : `$${plan.price_monthly}/mes`}
                                        </TableCell>
                                        <TableCell className="font-mono text-xs opacity-60">
                                            {plan.dlocal_plan_token
                                                ? `${plan.dlocal_plan_token.substring(0, 12)}...`
                                                : <span className="text-yellow-600">Local</span>
                                            }
                                        </TableCell>
                                        <TableCell>
                                            <Badge variant={plan.is_active ? "default" : "secondary"}>
                                                {plan.is_active ? 'Activo' : 'Inactivo'}
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
                                                                if (confirm(`¿Desactivar el plan "${plan.name}"?`)) {
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
                        Distribuidores y Accesos
                    </CardTitle>
                    <CardDescription>
                        Gestiona el acceso de todos los distribuidores registrados. Puedes otorgar o revocar la membresía de cortesía manualmente.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {isLoadingDistributors ? (
                        <div className="flex justify-center py-8">
                            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                        </div>
                    ) : !distributors?.length ? (
                        <div className="text-center py-12 text-muted-foreground">
                            No hay distribuidores registrados aún.
                        </div>
                    ) : (
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Distribuidor</TableHead>
                                    <TableHead>Email</TableHead>
                                    <TableHead>Plan Actual</TableHead>
                                    <TableHead>Suscripción</TableHead>
                                    <TableHead className="text-right">Licencia Cortesía</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {distributors.map((dist) => (
                                    <TableRow key={dist.id}>
                                        <TableCell>
                                            <div className="font-medium">{dist.name}</div>
                                            <div className="text-xs text-muted-foreground">
                                                Registrado: {new Date(dist.created_at).toLocaleDateString()}
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
                                                <Badge className="bg-green-500 tracking-wide text-[10px] uppercase">Activa</Badge>
                                            ) : (
                                                <Badge variant="secondary" className="tracking-wide text-[10px] uppercase">Inactiva</Badge>
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
                            Estado de Integración
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="flex items-center gap-2">
                            <CheckCircle2 className="h-5 w-5 text-green-500" />
                            <span className="font-medium">dLocal Go API Configurada</span>
                        </div>
                        <p className="text-xs text-muted-foreground mt-2">
                            El sistema se comunica con el entorno configurado en tu archivo .env.
                            Si las credenciales no están completas, los planes se guardarán solo localmente.
                        </p>
                    </CardContent>
                </Card>

                <Card className="bg-blue-500/5 border-blue-500/10">
                    <CardHeader>
                        <CardTitle className="text-sm flex items-center gap-2 text-blue-700">
                            <Users className="h-4 w-4" />
                            Cuentas de Cortesía
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-sm">
                            Las cuentas de cortesía evitan el proceso de pago completamente. 
                            Útil para VIPs, pruebas internas o distribuidores en periodo de gracia.
                        </p>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
