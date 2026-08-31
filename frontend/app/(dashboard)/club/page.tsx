'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
    Store,
    MapPin,
    Clock,
    Plus,
    Edit,
    Trash2,
    Share2,
    ExternalLink,
    Sparkles,
    Flame,
    Zap,
    Save,
    RefreshCw,
    ShoppingBag,
    UtensilsCrossed,
    Compass,
    Phone,
    Bot,
    MessageCircle,
    CheckCircle2,
    Sliders,
    Search,
    X,
    Loader2
} from 'lucide-react';
import { toast } from 'sonner';
import apiClient from '@/lib/api-client';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useAuthStore } from '@/store/use-auth-store';

interface ClubProduct {
    id: number;
    name: string;
    category: string;
    description: string;
    price: number;
    currency: string;
    image_url?: string;
    protein_grams?: number;
    calories?: number;
    preparation_time_min?: number;
    benefits?: string[];
    customization_options?: {
        flavors?: string[];
        toppings?: string[];
        temperature?: string[];
    };
    is_available: boolean;
}

interface ClubSettings {
    distributor_id: number;
    distributor_name: string;
    herbalife_id?: string;
    club_name: string;
    club_slogan: string;
    club_address: string;
    club_city: string;
    club_schedule: string;
    club_phone: string;
    club_latitude?: number;
    club_longitude?: number;
    club_banner_url?: string;
    club_logo_url?: string;
    club_is_active: boolean;
    club_amenities: string[];
    club_announcement?: string;
    google_maps_url: string;
    apple_maps_url: string;
}

interface ClubOrder {
    id: number;
    order_number: string;
    customer_name: string;
    customer_phone?: string;
    customer_email?: string;
    delivery_type: string;
    items: any[];
    subtotal: number;
    total: number;
    currency: string;
    notes?: string;
    status: string;
    created_at: string;
}

export default function NutritionClubDashboardPage() {
    const queryClient = useQueryClient();
    const user = useAuthStore((s) => s.user);

    const [activeTab, setActiveTab] = useState<string>('profile');
    const [searchMenu, setSearchMenu] = useState<string>('');
    const [selectedCategory, setSelectedCategory] = useState<string>('all');

    // Product Modal State (Create / Edit)
    const [productModalOpen, setProductModalOpen] = useState<boolean>(false);
    const [editingProduct, setEditingProduct] = useState<ClubProduct | null>(null);

    const [formName, setFormName] = useState<string>('');
    const [formCategory, setFormCategory] = useState<string>('batidos');
    const [formPrice, setFormPrice] = useState<string>('');
    const [formDescription, setFormDescription] = useState<string>('');
    const [formProtein, setFormProtein] = useState<string>('');
    const [formCalories, setFormCalories] = useState<string>('');
    const [formFlavors, setFormFlavors] = useState<string>('');
    const [formToppings, setFormToppings] = useState<string>('');
    const [formImageUrl, setFormImageUrl] = useState<string>('');
    const [formAvailable, setFormAvailable] = useState<boolean>(true);

    // Profile Settings Form State
    const [clubName, setClubName] = useState<string>('');
    const [clubSlogan, setClubSlogan] = useState<string>('');
    const [clubAddress, setClubAddress] = useState<string>('');
    const [clubCity, setClubCity] = useState<string>('');
    const [clubSchedule, setClubSchedule] = useState<string>('');
    const [clubPhone, setClubPhone] = useState<string>('');
    const [clubLat, setClubLat] = useState<string>('');
    const [clubLng, setClubLng] = useState<string>('');
    const [clubAmenities, setClubAmenities] = useState<string>('');
    const [clubAnnouncement, setClubAnnouncement] = useState<string>('');

    // Fetch Club Settings
    const { data: clubSettings, isLoading: isSettingsLoading } = useQuery({
        queryKey: ['club-settings'],
        queryFn: async () => {
            const res = await apiClient.get<{ data: ClubSettings }>('/club/settings');
            const data = res.data.data;
            setClubName(data.club_name || '');
            setClubSlogan(data.club_slogan || '');
            setClubAddress(data.club_address || '');
            setClubCity(data.club_city || '');
            setClubSchedule(data.club_schedule || '');
            setClubPhone(data.club_phone || '');
            setClubLat(data.club_latitude ? String(data.club_latitude) : '');
            setClubLng(data.club_longitude ? String(data.club_longitude) : '');
            setClubAmenities(data.club_amenities ? data.club_amenities.join(', ') : '');
            setClubAnnouncement(data.club_announcement || '');
            return data;
        },
    });

    // Fetch Products
    const { data: products = [], isLoading: isProductsLoading } = useQuery({
        queryKey: ['club-products'],
        queryFn: async () => {
            const res = await apiClient.get<{ data: ClubProduct[] }>('/club/products');
            return res.data.data;
        },
    });

    // Fetch Orders
    const { data: orders = [], isLoading: isOrdersLoading } = useQuery({
        queryKey: ['club-orders'],
        queryFn: async () => {
            const res = await apiClient.get<{ data: ClubOrder[] }>('/club/orders');
            return res.data.data;
        },
    });

    // Update Settings Mutation
    const updateSettingsMutation = useMutation({
        mutationFn: async () => {
            const payload = {
                club_name: clubName,
                club_slogan: clubSlogan,
                club_address: clubAddress,
                club_city: clubCity,
                club_schedule: clubSchedule,
                club_phone: clubPhone,
                club_latitude: clubLat ? parseFloat(clubLat) : null,
                club_longitude: clubLng ? parseFloat(clubLng) : null,
                club_amenities: clubAmenities.split(',').map((a) => a.trim()).filter(Boolean),
                club_announcement: clubAnnouncement,
            };
            const res = await apiClient.put('/club/settings', payload);
            return res.data.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['club-settings'] });
            toast.success('¡Configuración del Club guardada exitosamente!');
        },
        onError: (err: any) => {
            toast.error(err?.response?.data?.error || 'Error al guardar configuración');
        },
    });

    // Save Product Mutation (Create / Edit)
    const saveProductMutation = useMutation({
        mutationFn: async () => {
            const payload = {
                name: formName,
                category: formCategory,
                price: parseFloat(formPrice) || 0.0,
                description: formDescription,
                protein_grams: formProtein ? parseFloat(formProtein) : null,
                calories: formCalories ? parseInt(formCalories) : null,
                image_url: formImageUrl || undefined,
                is_available: formAvailable,
                customization_options: {
                    flavors: formFlavors.split(',').map((f) => f.trim()).filter(Boolean),
                    toppings: formToppings.split(',').map((t) => t.trim()).filter(Boolean),
                },
            };

            if (editingProduct) {
                const res = await apiClient.put(`/club/products/${editingProduct.id}`, payload);
                return res.data.data;
            } else {
                const res = await apiClient.post('/club/products', payload);
                return res.data.data;
            }
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['club-products'] });
            setProductModalOpen(false);
            setEditingProduct(null);
            toast.success(editingProduct ? 'Preparación actualizada' : 'Nueva preparación agregada');
        },
        onError: (err: any) => {
            toast.error(err?.response?.data?.error || 'Error al guardar producto');
        },
    });

    // Delete Product Mutation
    const deleteProductMutation = useMutation({
        mutationFn: async (id: number) => {
            await apiClient.delete(`/club/products/${id}`);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['club-products'] });
            toast.success('Preparación eliminada del menú');
        },
        onError: (err: any) => {
            toast.error(err?.response?.data?.error || 'Error al eliminar');
        },
    });

    // Seed Menu Mutation
    const seedMenuMutation = useMutation({
        mutationFn: async () => {
            const res = await apiClient.post('/club/seed-menu', {});
            return res.data;
        },
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ['club-products'] });
            toast.success(data?.message || '¡Menú típico de Club cargado exitosamente!');
        },
        onError: (err: any) => {
            toast.error(err?.response?.data?.error || 'Error al cargar menú');
        },
    });

    // Update Order Status Mutation
    const updateOrderStatusMutation = useMutation({
        mutationFn: async ({ orderId, status }: { orderId: number; status: string }) => {
            const res = await apiClient.put(`/club/orders/${orderId}/status`, { status });
            return res.data.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['club-orders'] });
            toast.success('Estado del pedido actualizado');
        },
    });

    // Open Modal for Create
    const handleOpenCreateProduct = () => {
        setEditingProduct(null);
        setFormName('');
        setFormCategory('batidos');
        setFormPrice('3.50');
        setFormDescription('');
        setFormProtein('24');
        setFormCalories('210');
        setFormFlavors('Cookies & Cream, Chocolate Belga, Fresa Silvestre, Vainilla');
        setFormToppings('Granola, Chía, Coco Tostado');
        setFormImageUrl('');
        setFormAvailable(true);
        setProductModalOpen(true);
    };

    // Open Modal for Edit
    const handleOpenEditProduct = (p: ClubProduct) => {
        setEditingProduct(p);
        setFormName(p.name);
        setFormCategory(p.category || 'batidos');
        setFormPrice(String(p.price));
        setFormDescription(p.description || '');
        setFormProtein(p.protein_grams ? String(p.protein_grams) : '');
        setFormCalories(p.calories ? String(p.calories) : '');
        setFormFlavors(p.customization_options?.flavors ? p.customization_options.flavors.join(', ') : '');
        setFormToppings(p.customization_options?.toppings ? p.customization_options.toppings.join(', ') : '');
        setFormImageUrl(p.image_url || '');
        setFormAvailable(p.is_available);
        setProductModalOpen(true);
    };

    const distributorRef = clubSettings?.herbalife_id || clubSettings?.distributor_id || user?.distributor_id || '';
    const publicUrl = typeof window !== 'undefined' ? `${window.location.origin}/club/${distributorRef}` : `https://enpi.click/club/${distributorRef}`;

    const handleCopyLink = () => {
        if (typeof window !== 'undefined') {
            navigator.clipboard.writeText(publicUrl);
            toast.success('¡Enlace del microsite copiado!');
        }
    };

    const filteredMenu = products.filter((p) => {
        const matchesCat = selectedCategory === 'all' || p.category === selectedCategory;
        const matchesSearch = !searchMenu ||
            p.name.toLowerCase().includes(searchMenu.toLowerCase()) ||
            (p.description && p.description.toLowerCase().includes(searchMenu.toLowerCase()));
        return matchesCat && matchesSearch;
    });

    return (
        <div className="space-y-6 max-w-6xl mx-auto pb-16">
            {/* Header with Title & Quick Links */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-1">
                    <div className="flex items-center gap-2">
                        <div className="flex h-9 w-9 items-center justify-center rounded-2xl bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 font-bold">
                            <Store className="h-5 w-5" />
                        </div>
                        <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-foreground">
                            Club de Nutrición & E-Commerce
                        </h1>
                    </div>
                    <p className="text-xs sm:text-sm text-muted-foreground">
                        Administra tu micrositio de ventas, ubicación en Google/Apple Maps, menú de preparaciones y pedidos.
                    </p>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={handleCopyLink}
                        className="rounded-xl text-xs gap-1.5 font-semibold"
                    >
                        <Share2 className="h-3.5 w-3.5" />
                        <span>Copiar Enlace</span>
                    </Button>
                    <Button
                        size="sm"
                        onClick={() => window.open(publicUrl, '_blank')}
                        className="rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs gap-1.5 shadow-md shadow-emerald-600/20"
                    >
                        <ExternalLink className="h-3.5 w-3.5" />
                        <span>Ver Micrositio</span>
                    </Button>
                </div>
            </div>

            {/* Navigation Tabs */}
            <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
                <TabsList className="grid grid-cols-4 max-w-2xl h-11 p-1 bg-muted/60 rounded-2xl border border-border/50">
                    <TabsTrigger value="profile" className="rounded-xl text-xs font-bold gap-1.5 data-[state=active]:bg-background data-[state=active]:shadow-sm">
                        <MapPin className="h-3.5 w-3.5" />
                        <span className="hidden sm:inline">Perfil & Ubicación</span>
                        <span className="sm:hidden">Perfil</span>
                    </TabsTrigger>
                    <TabsTrigger value="menu" className="rounded-xl text-xs font-bold gap-1.5 data-[state=active]:bg-background data-[state=active]:shadow-sm">
                        <UtensilsCrossed className="h-3.5 w-3.5" />
                        <span className="hidden sm:inline">Menú & Preparaciones</span>
                        <span className="sm:hidden">Menú</span>
                    </TabsTrigger>
                    <TabsTrigger value="orders" className="rounded-xl text-xs font-bold gap-1.5 data-[state=active]:bg-background data-[state=active]:shadow-sm">
                        <ShoppingBag className="h-3.5 w-3.5" />
                        <span>Pedidos ({orders.length})</span>
                    </TabsTrigger>
                    <TabsTrigger value="copilot" className="rounded-xl text-xs font-bold gap-1.5 data-[state=active]:bg-background data-[state=active]:shadow-sm">
                        <Bot className="h-3.5 w-3.5 text-indigo-500" />
                        <span>Copiloto IA</span>
                    </TabsTrigger>
                </TabsList>

                {/* ══════════════════════════════════════════════════════════════
                    TAB 1: PERFIL DEL CLUB & UBICACIÓN
                ══════════════════════════════════════════════════════════════ */}
                <TabsContent value="profile" className="space-y-6">
                    <Card className="rounded-3xl border-border/70 shadow-lg">
                        <CardHeader>
                            <CardTitle className="text-lg font-bold flex items-center gap-2">
                                <Store className="h-5 w-5 text-emerald-600" />
                                Información General del Club
                            </CardTitle>
                            <CardDescription className="text-xs">
                                Estos datos se mostrarán en la portada de tu micrositio y en los mensajes automáticos de pedido.
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-5">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div className="space-y-1.5">
                                    <Label className="text-xs font-bold">Nombre del Club *</Label>
                                    <Input
                                        placeholder="Ej: Club de Nutrición Bienestar Activo"
                                        value={clubName}
                                        onChange={(e) => setClubName(e.target.value)}
                                        className="rounded-xl text-xs"
                                    />
                                </div>
                                <div className="space-y-1.5">
                                    <Label className="text-xs font-bold">Teléfono / WhatsApp de Pedidos</Label>
                                    <Input
                                        placeholder="Ej: +593987654321"
                                        value={clubPhone}
                                        onChange={(e) => setClubPhone(e.target.value)}
                                        className="rounded-xl text-xs"
                                    />
                                </div>
                            </div>

                            <div className="space-y-1.5">
                                <Label className="text-xs font-bold">Eslogan o Mensaje de Bienvenida</Label>
                                <Input
                                    placeholder="Ej: Tu punto de encuentro para una nutrición saludable y energía total"
                                    value={clubSlogan}
                                    onChange={(e) => setClubSlogan(e.target.value)}
                                    className="rounded-xl text-xs"
                                />
                            </div>

                            <div className="space-y-1.5">
                                <Label className="text-xs font-bold">Anuncio Especial (Banner en la parte superior)</Label>
                                <Input
                                    placeholder="Ej: ¡Prueba hoy nuestro nuevo Waffle Proteico de Cheesecake de Fresa!"
                                    value={clubAnnouncement}
                                    onChange={(e) => setClubAnnouncement(e.target.value)}
                                    className="rounded-xl text-xs"
                                />
                            </div>

                            {/* Location & Maps Section */}
                            <div className="pt-4 border-t border-border/50 space-y-4">
                                <div className="space-y-1">
                                    <h4 className="font-bold text-sm flex items-center gap-1.5 text-foreground">
                                        <MapPin className="h-4 w-4 text-emerald-600" />
                                        Dirección y Geolocalización (Google Maps & Apple Maps)
                                    </h4>
                                    <p className="text-xs text-muted-foreground">
                                        El sistema genera botones interactivos para que tus prospectos y clientes abran la ruta de navegación en 1 clic.
                                    </p>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    <div className="md:col-span-2 space-y-1.5">
                                        <Label className="text-xs font-bold">Dirección Física del Club</Label>
                                        <Input
                                            placeholder="Ej: Av. Naciones Unidas y Amazonas, Local 102"
                                            value={clubAddress}
                                            onChange={(e) => setClubAddress(e.target.value)}
                                            className="rounded-xl text-xs"
                                        />
                                    </div>
                                    <div className="space-y-1.5">
                                        <Label className="text-xs font-bold">Ciudad</Label>
                                        <Input
                                            placeholder="Ej: Quito"
                                            value={clubCity}
                                            onChange={(e) => setClubCity(e.target.value)}
                                            className="rounded-xl text-xs"
                                        />
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="space-y-1.5">
                                        <Label className="text-xs font-bold">Horarios de Atención</Label>
                                        <Input
                                            placeholder="Ej: Lunes a Viernes: 07:00 - 12:00 y 16:00 - 19:30 | Sábados: 08:00 - 13:00"
                                            value={clubSchedule}
                                            onChange={(e) => setClubSchedule(e.target.value)}
                                            className="rounded-xl text-xs"
                                        />
                                    </div>
                                    <div className="space-y-1.5">
                                        <Label className="text-xs font-bold">Servicios / Amenidades (Separados por coma)</Label>
                                        <Input
                                            placeholder="Ej: Wi-Fi, Barra Proteica, Degustación Gratis, Aire Acondicionado"
                                            value={clubAmenities}
                                            onChange={(e) => setClubAmenities(e.target.value)}
                                            className="rounded-xl text-xs"
                                        />
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="space-y-1.5">
                                        <Label className="text-xs font-bold">Latitud GPS (Opcional para máxima precisión)</Label>
                                        <Input
                                            placeholder="Ej: -0.1785"
                                            value={clubLat}
                                            onChange={(e) => setClubLat(e.target.value)}
                                            className="rounded-xl text-xs"
                                        />
                                    </div>
                                    <div className="space-y-1.5">
                                        <Label className="text-xs font-bold">Longitud GPS (Opcional)</Label>
                                        <Input
                                            placeholder="Ej: -78.4852"
                                            value={clubLng}
                                            onChange={(e) => setClubLng(e.target.value)}
                                            className="rounded-xl text-xs"
                                        />
                                    </div>
                                </div>

                                {/* Map Links Live Preview */}
                                <div className="flex flex-wrap gap-3 pt-2">
                                    {clubSettings?.google_maps_url && (
                                        <Button
                                            type="button"
                                            variant="outline"
                                            size="sm"
                                            onClick={() => window.open(clubSettings.google_maps_url, '_blank')}
                                            className="rounded-xl text-xs gap-1.5"
                                        >
                                            <MapPin className="h-3.5 w-3.5 text-emerald-600" />
                                            <span>Probar Enlace de Google Maps</span>
                                        </Button>
                                    )}
                                    {clubSettings?.apple_maps_url && (
                                        <Button
                                            type="button"
                                            variant="outline"
                                            size="sm"
                                            onClick={() => window.open(clubSettings.apple_maps_url, '_blank')}
                                            className="rounded-xl text-xs gap-1.5"
                                        >
                                            <Compass className="h-3.5 w-3.5 text-teal-500" />
                                            <span>Probar Enlace de Apple Maps</span>
                                        </Button>
                                    )}
                                </div>
                            </div>

                            <div className="pt-4 flex justify-end">
                                <Button
                                    onClick={() => updateSettingsMutation.mutate()}
                                    disabled={updateSettingsMutation.isPending}
                                    className="rounded-2xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs h-11 px-6 shadow-md shadow-emerald-600/20 gap-2"
                                >
                                    {updateSettingsMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                                    <span>Guardar Configuración</span>
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* ══════════════════════════════════════════════════════════════
                    TAB 2: MENÚ & PREPARACIONES (CATÁLOGO)
                ══════════════════════════════════════════════════════════════ */}
                <TabsContent value="menu" className="space-y-6">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                        <div className="flex items-center gap-2">
                            <Input
                                placeholder="Buscar en el menú..."
                                value={searchMenu}
                                onChange={(e) => setSearchMenu(e.target.value)}
                                className="rounded-xl text-xs w-64 bg-muted/40 h-9"
                            />
                        </div>

                        <div className="flex flex-wrap items-center gap-2">
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => seedMenuMutation.mutate()}
                                disabled={seedMenuMutation.isPending}
                                className="rounded-xl text-xs gap-1.5 font-semibold text-emerald-600 dark:text-emerald-400 border-emerald-500/30"
                            >
                                <Sparkles className="h-3.5 w-3.5" />
                                <span>Cargar Menú Típico (1 Clic)</span>
                            </Button>
                            <Button
                                size="sm"
                                onClick={handleOpenCreateProduct}
                                className="rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs gap-1.5 shadow-md shadow-emerald-600/20"
                            >
                                <Plus className="h-3.5 w-3.5" />
                                <span>Nueva Preparación</span>
                            </Button>
                        </div>
                    </div>

                    {/* Products Grid */}
                    {filteredMenu.length === 0 ? (
                        <Card className="rounded-3xl border-dashed border-border/80 p-10 text-center space-y-4">
                            <UtensilsCrossed className="mx-auto h-12 w-12 text-muted-foreground/50" />
                            <div className="space-y-1">
                                <h3 className="font-bold text-base text-foreground">Tu menú aún no tiene productos</h3>
                                <p className="text-xs text-muted-foreground max-w-sm mx-auto">
                                    Puedes cargar automáticamente las 8 preparaciones estándar de club con 1 clic o agregar tus propias recetas personalizadas.
                                </p>
                            </div>
                            <div className="flex justify-center gap-3">
                                <Button
                                    onClick={() => seedMenuMutation.mutate()}
                                    className="rounded-2xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-md"
                                >
                                    <Sparkles className="h-3.5 w-3.5 mr-1.5" />
                                    Cargar Menú Típico de Club
                                </Button>
                            </div>
                        </Card>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {filteredMenu.map((p) => (
                                <Card key={p.id} className="rounded-3xl border border-border/60 overflow-hidden bg-card/60 backdrop-blur-sm shadow-sm hover:shadow-md transition-all flex flex-col justify-between">
                                    <div>
                                        <div className="h-36 w-full overflow-hidden bg-muted relative">
                                            {p.image_url ? (
                                                <img src={p.image_url} alt={p.name} className="h-full w-full object-cover" />
                                            ) : (
                                                <div className="h-full w-full flex items-center justify-center text-3xl">
                                                    🥤
                                                </div>
                                            )}
                                            <div className="absolute top-2 right-2">
                                                <Badge className={cn('text-[10px] font-bold border-none', p.is_available ? 'bg-emerald-600 text-white' : 'bg-destructive text-white')}>
                                                    {p.is_available ? 'Disponible' : 'Agotado'}
                                                </Badge>
                                            </div>
                                            <div className="absolute bottom-2 left-2 flex gap-1">
                                                {p.protein_grams && (
                                                    <span className="rounded-md bg-black/60 text-white px-2 py-0.5 text-[10px] font-bold backdrop-blur-md">
                                                        ⚡ {p.protein_grams}g Pro
                                                    </span>
                                                )}
                                                {p.calories && (
                                                    <span className="rounded-md bg-black/60 text-white px-2 py-0.5 text-[10px] font-bold backdrop-blur-md">
                                                        🔥 {p.calories} kcal
                                                    </span>
                                                )}
                                            </div>
                                        </div>

                                        <CardContent className="p-4 space-y-2">
                                            <div className="flex items-start justify-between gap-2">
                                                <h3 className="font-extrabold text-sm text-foreground line-clamp-1">{p.name}</h3>
                                                <span className="font-black text-emerald-600 dark:text-emerald-400 text-sm">
                                                    ${p.price.toFixed(2)}
                                                </span>
                                            </div>
                                            <p className="text-xs text-muted-foreground line-clamp-2">{p.description}</p>
                                            {p.customization_options?.flavors && p.customization_options.flavors.length > 0 && (
                                                <p className="text-[11px] text-muted-foreground truncate">
                                                    <span className="font-semibold text-foreground">Sabores:</span> {p.customization_options.flavors.join(', ')}
                                                </p>
                                            )}
                                        </CardContent>
                                    </div>

                                    <div className="p-4 pt-0 flex items-center justify-between border-t border-border/40 mt-2">
                                        <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-wider">{p.category}</span>
                                        <div className="flex items-center gap-1.5">
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                onClick={() => handleOpenEditProduct(p)}
                                                className="h-8 w-8 rounded-xl"
                                            >
                                                <Edit className="h-3.5 w-3.5 text-muted-foreground" />
                                            </Button>
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                onClick={() => {
                                                    if (confirm(`¿Eliminar ${p.name}?`)) {
                                                        deleteProductMutation.mutate(p.id);
                                                    }
                                                }}
                                                className="h-8 w-8 rounded-xl hover:text-destructive"
                                            >
                                                <Trash2 className="h-3.5 w-3.5" />
                                            </Button>
                                        </div>
                                    </div>
                                </Card>
                            ))}
                        </div>
                    )}
                </TabsContent>

                {/* ══════════════════════════════════════════════════════════════
                    TAB 3: PEDIDOS DEL CLUB
                ══════════════════════════════════════════════════════════════ */}
                <TabsContent value="orders" className="space-y-6">
                    <Card className="rounded-3xl border-border/70 shadow-lg">
                        <CardHeader>
                            <CardTitle className="text-lg font-bold flex items-center gap-2">
                                <ShoppingBag className="h-5 w-5 text-emerald-600" />
                                Registro de Pedidos del Micrositio
                            </CardTitle>
                            <CardDescription className="text-xs">
                                Todos los pedidos recibidos a través de tu catálogo en línea con detalle de preparaciones y personalizaciones.
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            {orders.length === 0 ? (
                                <div className="py-12 text-center space-y-2">
                                    <ShoppingBag className="mx-auto h-10 w-10 text-muted-foreground/40" />
                                    <p className="font-bold text-sm text-foreground">No hay pedidos registrados todavía</p>
                                    <p className="text-xs text-muted-foreground max-w-sm mx-auto">
                                        Comparte el enlace de tu club con tus prospectos y clientes en redes sociales o WhatsApp para empezar a recibir órdenes.
                                    </p>
                                </div>
                            ) : (
                                <div className="divide-y divide-border/50">
                                    {orders.map((order) => (
                                        <div key={order.id} className="py-4 first:pt-0 flex flex-col md:flex-row md:items-center justify-between gap-4">
                                            <div className="space-y-1.5 text-xs">
                                                <div className="flex items-center gap-2">
                                                    <Badge variant="outline" className="font-black text-xs">
                                                        #{order.order_number}
                                                    </Badge>
                                                    <span className="font-bold text-sm text-foreground">{order.customer_name}</span>
                                                    {order.customer_phone && (
                                                        <span className="text-muted-foreground">• 📱 {order.customer_phone}</span>
                                                    )}
                                                    <Badge className="bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-none font-bold text-[10px]">
                                                        {order.delivery_type === 'dine_in' ? '🍽️ En Club' : order.delivery_type === 'pickup' ? '🥡 Para Llevar' : '🛵 Domicilio'}
                                                    </Badge>
                                                </div>

                                                <div className="text-muted-foreground pl-1 space-y-0.5">
                                                    {order.items?.map((it: any, i: number) => (
                                                        <p key={i}>
                                                            • <span className="font-bold text-foreground">{it.quantity}x {it.name}</span>
                                                            {it.flavor && ` (Sabor: ${it.flavor})`}
                                                            {it.toppings?.length > 0 && ` [Toppings: ${it.toppings.join(', ')}]`}
                                                            {it.notes && ` - "${it.notes}"`}
                                                        </p>
                                                    ))}
                                                </div>

                                                {order.notes && (
                                                    <p className="text-[11px] text-muted-foreground italic pl-1">
                                                        Nota: "{order.notes}"
                                                    </p>
                                                )}
                                                <p className="text-[10px] text-muted-foreground pl-1">
                                                    Fecha: {new Date(order.created_at).toLocaleString()}
                                                </p>
                                            </div>

                                            <div className="flex items-center gap-3 shrink-0">
                                                <div className="text-right">
                                                    <p className="text-[10px] text-muted-foreground font-semibold">Total</p>
                                                    <p className="text-base font-black text-emerald-600 dark:text-emerald-400">
                                                        ${order.total.toFixed(2)} {order.currency}
                                                    </p>
                                                </div>

                                                <Select
                                                    value={order.status}
                                                    onValueChange={(val) => updateOrderStatusMutation.mutate({ orderId: order.id, status: val })}
                                                >
                                                    <SelectTrigger className="w-32 h-9 text-xs rounded-xl font-bold">
                                                        <SelectValue />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        <SelectItem value="pending">🟡 Pendiente</SelectItem>
                                                        <SelectItem value="confirmed">🟢 Confirmado</SelectItem>
                                                        <SelectItem value="preparing">🥣 Preparando</SelectItem>
                                                        <SelectItem value="ready">✅ Listo</SelectItem>
                                                        <SelectItem value="delivered">🎉 Entregado</SelectItem>
                                                        <SelectItem value="cancelled">❌ Cancelado</SelectItem>
                                                    </SelectContent>
                                                </Select>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* ══════════════════════════════════════════════════════════════
                    TAB 4: COPILOTO IA PARA CLUB
                ══════════════════════════════════════════════════════════════ */}
                <TabsContent value="copilot" className="space-y-6">
                    <Card className="rounded-3xl border-border/70 shadow-lg bg-gradient-to-br from-card via-card to-emerald-500/5">
                        <CardHeader>
                            <div className="flex items-center gap-2">
                                <div className="w-8 h-8 rounded-xl bg-indigo-500/10 flex items-center justify-center text-indigo-600 font-bold">
                                    <Bot className="w-5 h-5" />
                                </div>
                                <CardTitle className="text-lg font-bold">
                                    Gestión del Club con tu Copiloto IA
                                </CardTitle>
                            </div>
                            <CardDescription className="text-xs">
                                Tu agente de IA te ayuda a administrar tu Club de Nutrición mediante notas de voz o texto tanto desde el chat de la plataforma como escribiendo a tu WhatsApp vinculado.
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-5">
                            <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-950 dark:text-emerald-200 space-y-2">
                                <p className="font-bold flex items-center gap-1.5">
                                    <Sparkles className="w-4 h-4 text-emerald-600" />
                                    ¿Qué puedes pedirle a tu Copiloto por WhatsApp o en la plataforma?
                                </p>
                                <p className="leading-relaxed">
                                    Solo habla o escribe con naturalidad desde tu número de distribuidor vinculado y tu asistente ejecutará las acciones en tiempo real:
                                </p>
                            </div>

                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 text-xs">
                                <div className="p-4 rounded-2xl bg-muted/40 border border-border/50 space-y-1.5">
                                    <p className="font-bold text-foreground flex items-center gap-1.5">
                                        🥤 "Crea un Waffle Proteico de Vainilla a $4.50 con 26g de proteína"
                                    </p>
                                    <p className="text-muted-foreground text-[11px]">
                                        El agente creará la preparación en tu menú al instante.
                                    </p>
                                </div>
                                <div className="p-4 rounded-2xl bg-muted/40 border border-border/50 space-y-1.5">
                                    <p className="font-bold text-foreground flex items-center gap-1.5">
                                        ⏰ "Actualiza el horario del club de 7am a 12pm y de 4pm a 7pm"
                                    </p>
                                    <p className="text-muted-foreground text-[11px]">
                                        Actualiza los horarios y el estatus visible en tu micrositio.
                                    </p>
                                </div>
                                <div className="p-4 rounded-2xl bg-muted/40 border border-border/50 space-y-1.5">
                                    <p className="font-bold text-foreground flex items-center gap-1.5">
                                        📍 "Pásame la ubicación y el enlace de mi club para un cliente"
                                    </p>
                                    <p className="text-muted-foreground text-[11px]">
                                        Te enviará los enlaces directos de Google Maps, Apple Maps y el menú.
                                    </p>
                                </div>
                                <div className="p-4 rounded-2xl bg-muted/40 border border-border/50 space-y-1.5">
                                    <p className="font-bold text-foreground flex items-center gap-1.5">
                                        💰 "Cambia el precio del Mega Té a $3.00 y desactiva el batido de fresa"
                                    </p>
                                    <p className="text-muted-foreground text-[11px]">
                                        Modifica precios y stock en segundos sin entrar al panel.
                                    </p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>

            {/* ══════════════════════════════════════════════════════════════════
                MODAL: CREAR / EDITAR PREPARACIÓN
            ══════════════════════════════════════════════════════════════════ */}
            <Dialog open={productModalOpen} onOpenChange={setProductModalOpen}>
                <DialogContent className="rounded-3xl max-w-lg p-6 max-h-[90vh] overflow-y-auto">
                    <DialogHeader>
                        <DialogTitle className="text-xl font-bold">
                            {editingProduct ? 'Editar Preparación del Club' : 'Nueva Preparación / Receta'}
                        </DialogTitle>
                        <DialogDescription className="text-xs text-muted-foreground">
                            Configura los detalles nutricionales, sabores disponibles y precio en el menú.
                        </DialogDescription>
                    </DialogHeader>

                    <div className="space-y-4 pt-2">
                        <div className="space-y-1.5">
                            <Label className="text-xs font-bold">Nombre de la Preparación *</Label>
                            <Input
                                placeholder="Ej: Waffle Proteico Gourmet de Chocolate"
                                value={formName}
                                onChange={(e) => setFormName(e.target.value)}
                                className="rounded-xl text-xs"
                            />
                        </div>

                        <div className="grid grid-cols-2 gap-3">
                            <div className="space-y-1.5">
                                <Label className="text-xs font-bold">Categoría *</Label>
                                <Select value={formCategory} onValueChange={setFormCategory}>
                                    <SelectTrigger className="rounded-xl text-xs h-10">
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="batidos">🥤 Batidos Proteicos</SelectItem>
                                        <SelectItem value="tes_bebidas">🍵 Tés & Bebidas Herbales</SelectItem>
                                        <SelectItem value="waffles_bowls">🧇 Waffles & Bowls</SelectItem>
                                        <SelectItem value="combos">🥣 Combos 3 Pasos</SelectItem>
                                        <SelectItem value="snacks">🥗 Snacks & Suplementos</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="space-y-1.5">
                                <Label className="text-xs font-bold">Precio ($ USD) *</Label>
                                <Input
                                    type="number"
                                    step="0.25"
                                    placeholder="Ej: 4.50"
                                    value={formPrice}
                                    onChange={(e) => setFormPrice(e.target.value)}
                                    className="rounded-xl text-xs"
                                />
                            </div>
                        </div>

                        <div className="space-y-1.5">
                            <Label className="text-xs font-bold">Descripción / Beneficios</Label>
                            <Textarea
                                placeholder="Ej: Waffle crujiente con 26g de proteína, cero harinas refinadas..."
                                value={formDescription}
                                onChange={(e) => setFormDescription(e.target.value)}
                                className="rounded-xl text-xs resize-none h-16"
                            />
                        </div>

                        <div className="grid grid-cols-2 gap-3">
                            <div className="space-y-1.5">
                                <Label className="text-xs font-bold">Gramos de Proteína (g)</Label>
                                <Input
                                    type="number"
                                    placeholder="Ej: 24"
                                    value={formProtein}
                                    onChange={(e) => setFormProtein(e.target.value)}
                                    className="rounded-xl text-xs"
                                />
                            </div>
                            <div className="space-y-1.5">
                                <Label className="text-xs font-bold">Calorías (kcal)</Label>
                                <Input
                                    type="number"
                                    placeholder="Ej: 210"
                                    value={formCalories}
                                    onChange={(e) => setFormCalories(e.target.value)}
                                    className="rounded-xl text-xs"
                                />
                            </div>
                        </div>

                        <div className="space-y-1.5">
                            <Label className="text-xs font-bold">Sabores Disponibles (Separados por coma)</Label>
                            <Input
                                placeholder="Ej: Cookies & Cream, Chocolate, Fresa, Vainilla"
                                value={formFlavors}
                                onChange={(e) => setFormFlavors(e.target.value)}
                                className="rounded-xl text-xs"
                            />
                        </div>

                        <div className="space-y-1.5">
                            <Label className="text-xs font-bold">Toppings Opcionales (Separados por coma)</Label>
                            <Input
                                placeholder="Ej: Granola, Semillas de Chía, Coco Rallado, Frutos Rojos"
                                value={formToppings}
                                onChange={(e) => setFormToppings(e.target.value)}
                                className="rounded-xl text-xs"
                            />
                        </div>

                        <div className="space-y-1.5">
                            <Label className="text-xs font-bold">URL de la Foto (Opcional)</Label>
                            <Input
                                placeholder="https://..."
                                value={formImageUrl}
                                onChange={(e) => setFormImageUrl(e.target.value)}
                                className="rounded-xl text-xs"
                            />
                        </div>

                        <div className="flex items-center justify-between pt-2 border-t border-border/50">
                            <div className="space-y-0.5">
                                <Label className="text-xs font-bold">Disponible en el Menú</Label>
                                <p className="text-[11px] text-muted-foreground">Si está activo, los clientes podrán pedirlo</p>
                            </div>
                            <Switch checked={formAvailable} onCheckedChange={setFormAvailable} />
                        </div>
                    </div>

                    <DialogFooter className="pt-4">
                        <Button variant="outline" onClick={() => setProductModalOpen(false)} className="rounded-xl text-xs">
                            Cancelar
                        </Button>
                        <Button
                            onClick={() => saveProductMutation.mutate()}
                            disabled={!formName.trim() || saveProductMutation.isPending}
                            className="rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs"
                        >
                            {saveProductMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4 mr-1.5" />}
                            <span>Guardar</span>
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
