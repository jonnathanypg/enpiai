'use client';

import { useState, useMemo } from 'react';
import { useParams } from 'next/navigation';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
    Store,
    MapPin,
    Clock,
    Phone,
    Share2,
    ShoppingBag,
    Plus,
    Minus,
    Trash2,
    CheckCircle2,
    Sparkles,
    Flame,
    Zap,
    Heart,
    MessageCircle,
    Navigation,
    Compass,
    Check,
    Search,
    ChevronRight,
    X,
    UtensilsCrossed,
    Loader2
} from 'lucide-react';
import { toast } from 'sonner';
import apiClient from '@/lib/api-client';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetFooter, SheetDescription } from '@/components/ui/sheet';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { ThemeToggle } from '@/components/shared/theme-toggle';

interface CustomizationOptions {
    flavors?: string[];
    toppings?: string[];
    temperature?: string[];
    extras?: { name: string; price: number }[];
}

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
    customization_options?: CustomizationOptions;
    is_available: boolean;
}

interface ClubData {
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
    instagram?: string;
    facebook?: string;
}

interface CategoryItem {
    id: string;
    label: string;
    icon: string;
}

interface CartItem {
    cart_item_id: string;
    product_id: number;
    name: string;
    unit_price: number;
    quantity: number;
    flavor?: string;
    toppings: string[];
    temperature?: string;
    notes?: string;
    total: number;
    image_url?: string;
}

export default function NutritionClubMicrosite() {
    const params = useParams();
    const distributor_ref = (params?.distributor_id as string) || '';

    const [selectedCategory, setSelectedCategory] = useState<string>('all');
    const [searchQuery, setSearchQuery] = useState<string>('');
    const [cart, setCart] = useState<CartItem[]>([]);
    const [isCartOpen, setIsCartOpen] = useState<boolean>(false);

    // Customization Modal State
    const [activeProduct, setActiveProduct] = useState<ClubProduct | null>(null);
    const [modalFlavor, setModalFlavor] = useState<string>('');
    const [modalToppings, setModalToppings] = useState<string[]>([]);
    const [modalTemperature, setModalTemperature] = useState<string>('');
    const [modalNotes, setModalNotes] = useState<string>('');
    const [modalQuantity, setModalQuantity] = useState<number>(1);

    // Checkout State
    const [customerName, setCustomerName] = useState<string>('');
    const [customerPhone, setCustomerPhone] = useState<string>('');
    const [customerEmail, setCustomerEmail] = useState<string>('');
    const [deliveryType, setDeliveryType] = useState<string>('dine_in'); // dine_in, pickup, delivery
    const [orderNotes, setOrderNotes] = useState<string>('');
    const [orderSuccessData, setOrderSuccessData] = useState<{ orderNumber: string; whatsappUrl: string } | null>(null);

    // Fetch Public Club Data
    const { data: clubResponse, isLoading, isError } = useQuery({
        queryKey: ['public-club', distributor_ref],
        queryFn: async () => {
            const res = await apiClient.get(`/club/public/${distributor_ref}`);
            return res.data?.data as {
                club: ClubData;
                categories: CategoryItem[];
                products: ClubProduct[];
            };
        },
        enabled: Boolean(distributor_ref),
    });

    const club = clubResponse?.club;
    const categories = clubResponse?.categories || [];
    const products = clubResponse?.products || [];

    // Filter Products
    const filteredProducts = useMemo(() => {
        return products.filter((p) => {
            const matchesCat = selectedCategory === 'all' || p.category === selectedCategory;
            const matchesSearch = !searchQuery ||
                p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                (p.description && p.description.toLowerCase().includes(searchQuery.toLowerCase()));
            return matchesCat && matchesSearch;
        });
    }, [products, selectedCategory, searchQuery]);

    // Cart calculations
    const cartCount = cart.reduce((sum, item) => sum + item.quantity, 0);
    const cartSubtotal = cart.reduce((sum, item) => sum + item.total, 0);

    // Open Customization Modal
    const handleOpenCustomize = (product: ClubProduct) => {
        setActiveProduct(product);
        const flavors = product.customization_options?.flavors;
        const temps = product.customization_options?.temperature;
        setModalFlavor(flavors && flavors.length > 0 ? flavors[0] : '');
        setModalTemperature(temps && temps.length > 0 ? temps[0] : '');
        setModalToppings([]);
        setModalNotes('');
        setModalQuantity(1);
    };

    // Toggle Topping in Modal
    const toggleTopping = (topping: string) => {
        setModalToppings((prev) =>
            prev.includes(topping) ? prev.filter((t) => t !== topping) : [...prev, topping]
        );
    };

    // Add to Cart
    const handleAddToCart = () => {
        if (!activeProduct) return;

        const cartItemId = `${activeProduct.id}-${modalFlavor}-${modalToppings.sort().join(',')}-${modalTemperature}-${Date.now()}`;
        const itemTotal = activeProduct.price * modalQuantity;

        const newItem: CartItem = {
            cart_item_id: cartItemId,
            product_id: activeProduct.id,
            name: activeProduct.name,
            unit_price: activeProduct.price,
            quantity: modalQuantity,
            flavor: modalFlavor || undefined,
            toppings: modalToppings,
            temperature: modalTemperature || undefined,
            notes: modalNotes || undefined,
            total: itemTotal,
            image_url: activeProduct.image_url,
        };

        setCart((prev) => [...prev, newItem]);
        setActiveProduct(null);
        toast.success(`¡${newItem.name} agregado al pedido!`, {
            description: `${modalQuantity}x por $${itemTotal.toFixed(2)}`,
        });
    };

    // Remove from Cart
    const handleRemoveFromCart = (cartItemId: string) => {
        setCart((prev) => prev.filter((i) => i.cart_item_id !== cartItemId));
    };

    // Update Quantity in Cart
    const handleUpdateCartQty = (cartItemId: string, delta: number) => {
        setCart((prev) =>
            prev
                .map((item) => {
                    if (item.cart_item_id === cartItemId) {
                        const newQty = item.quantity + delta;
                        if (newQty <= 0) return null;
                        return {
                            ...item,
                            quantity: newQty,
                            total: newQty * item.unit_price,
                        };
                    }
                    return item;
                })
                .filter(Boolean) as CartItem[]
        );
    };

    // Submit Order Mutation
    const orderMutation = useMutation({
        mutationFn: async () => {
            const payload = {
                customer_name: customerName,
                customer_phone: customerPhone,
                customer_email: customerEmail,
                delivery_type: deliveryType,
                items: cart,
                subtotal: cartSubtotal,
                total: cartSubtotal,
                notes: orderNotes,
                currency: 'USD',
            };
            const res = await apiClient.post(`/club/public/${distributor_ref}/order`, payload);
            return res.data?.data;
        },
        onSuccess: (data) => {
            const orderNum = data?.order?.order_number || 'CN-CONFIRMED';
            const waUrl = data?.whatsapp_url || '';
            setOrderSuccessData({
                orderNumber: orderNum,
                whatsappUrl: waUrl,
            });
            setCart([]);
            setIsCartOpen(false);
            if (waUrl && typeof window !== 'undefined') {
                window.open(waUrl, '_blank');
            }
        },
        onError: (err: any) => {
            const msg = err?.response?.data?.error || 'Error al procesar el pedido';
            toast.error(msg);
        },
    });

    const handleShareClub = () => {
        if (typeof window !== 'undefined') {
            navigator.clipboard.writeText(window.location.href);
            toast.success('¡Enlace del club copiado al portapapeles!');
        }
    };

    if (isLoading) {
        return (
            <div className="flex min-h-screen flex-col items-center justify-center space-y-4 p-4">
                <div className="relative flex items-center justify-center">
                    <div className="h-16 w-16 animate-ping rounded-full bg-emerald-500/20" />
                    <Store className="relative h-8 w-8 animate-bounce text-emerald-600 dark:text-emerald-400" />
                </div>
                <p className="text-sm font-semibold text-muted-foreground animate-pulse">
                    Cargando Club de Nutrición y Menú...
                </p>
            </div>
        );
    }

    if (isError || !club) {
        return (
            <div className="flex min-h-screen flex-col items-center justify-center p-4 text-center">
                <div className="rounded-3xl border border-destructive/20 bg-destructive/10 p-8 max-w-md space-y-3">
                    <Store className="mx-auto h-12 w-12 text-destructive" />
                    <h2 className="text-xl font-bold text-foreground">Club no encontrado</h2>
                    <p className="text-xs text-muted-foreground">
                        No pudimos encontrar el Club de Nutrición solicitado. Por favor verifica el enlace proporcionado por tu distribuidor.
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-background text-foreground pb-24">
            {/* Top Navigation Bar */}
            <header className="sticky top-0 z-40 w-full border-b border-border/40 bg-background/80 backdrop-blur-xl">
                <div className="mx-auto flex h-16 max-w-5xl items-center justify-between px-4">
                    <div className="flex items-center gap-3">
                        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-tr from-emerald-500 to-teal-400 text-white shadow-md shadow-emerald-500/20 font-black text-sm">
                            🌿
                        </div>
                        <div className="truncate">
                            <h1 className="text-sm sm:text-base font-extrabold tracking-tight truncate">
                                {club.club_name}
                            </h1>
                            <p className="text-[11px] text-muted-foreground truncate">
                                Coach: {club.distributor_name}
                            </p>
                        </div>
                    </div>

                    <div className="flex items-center gap-2">
                        <ThemeToggle />
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={handleShareClub}
                            className="rounded-xl h-9 gap-1.5 text-xs font-semibold"
                        >
                            <Share2 className="h-3.5 w-3.5" />
                            <span className="hidden sm:inline">Compartir</span>
                        </Button>
                        {cartCount > 0 && (
                            <Button
                                size="sm"
                                onClick={() => setIsCartOpen(true)}
                                className="rounded-xl h-9 gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-md shadow-emerald-600/20"
                            >
                                <ShoppingBag className="h-3.5 w-3.5" />
                                <span>{cartCount}</span>
                                <span className="hidden sm:inline">• ${cartSubtotal.toFixed(2)}</span>
                            </Button>
                        )}
                    </div>
                </div>
            </header>

            {/* Announcement Alert (if present) */}
            {club.club_announcement && (
                <div className="bg-gradient-to-r from-emerald-600 to-teal-600 text-white px-4 py-2 text-center text-xs font-semibold tracking-wide shadow-inner">
                    ✨ {club.club_announcement}
                </div>
            )}

            <main className="mx-auto max-w-5xl px-4 py-6 md:py-8 space-y-8">
                {/* Hero Profile & Location Section */}
                <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-emerald-700 via-teal-800 to-slate-950 p-6 md:p-10 text-white shadow-2xl">
                    <div className="absolute top-0 right-0 -mt-8 -mr-8 h-48 w-48 rounded-full bg-white/10 blur-3xl" />
                    <div className="relative z-10 space-y-6">
                        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                            <div className="space-y-3">
                                <div className="flex flex-wrap items-center gap-2">
                                    <Badge className="bg-white/20 text-white border-none font-bold text-xs backdrop-blur-md">
                                        <Sparkles className="w-3 h-3 mr-1 text-emerald-300" />
                                        Club de Nutrición Oficial
                                    </Badge>
                                    <Badge className="bg-emerald-400/20 text-emerald-200 border border-emerald-400/30 text-xs font-semibold">
                                        Abierto Hoy
                                    </Badge>
                                </div>
                                <h2 className="text-2xl md:text-4xl font-black tracking-tight">
                                    {club.club_name}
                                </h2>
                                <p className="text-sm md:text-base text-emerald-100 max-w-xl leading-relaxed">
                                    {club.club_slogan}
                                </p>
                            </div>

                            {/* Location Action Buttons (Google Maps & Apple Maps) */}
                            <div className="flex flex-col sm:flex-row md:flex-col gap-2.5 shrink-0">
                                {club.google_maps_url && (
                                    <Button
                                        size="sm"
                                        onClick={() => window.open(club.google_maps_url, '_blank')}
                                        className="rounded-2xl bg-white text-slate-950 hover:bg-slate-100 font-bold text-xs h-10 shadow-lg justify-center gap-2"
                                    >
                                        <MapPin className="h-4 w-4 text-emerald-600" />
                                        <span>Abrir en Google Maps</span>
                                    </Button>
                                )}
                                {club.apple_maps_url && (
                                    <Button
                                        size="sm"
                                        variant="outline"
                                        onClick={() => window.open(club.apple_maps_url, '_blank')}
                                        className="rounded-2xl border-white/40 text-white hover:bg-white/15 font-bold text-xs h-10 backdrop-blur-md justify-center gap-2"
                                    >
                                        <Compass className="h-4 w-4 text-teal-300" />
                                        <span>Abrir en Apple Maps</span>
                                    </Button>
                                )}
                                {club.club_phone && (
                                    <Button
                                        size="sm"
                                        variant="ghost"
                                        onClick={() => {
                                            const clean = club.club_phone.replace(/\D/g, '');
                                            window.open(`https://wa.me/${clean}?text=Hola!%20Deseo%20información%20del%20Club`, '_blank');
                                        }}
                                        className="rounded-2xl text-emerald-200 hover:text-white hover:bg-white/10 font-bold text-xs h-10 justify-center gap-2"
                                    >
                                        <MessageCircle className="h-4 w-4" />
                                        <span>WhatsApp del Club</span>
                                    </Button>
                                )}
                            </div>
                        </div>

                        {/* Address and Hours Info Bar */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 pt-2 border-t border-white/15 text-xs text-emerald-100">
                            {club.club_address && (
                                <div className="flex items-start gap-2">
                                    <MapPin className="h-4 w-4 shrink-0 text-emerald-300 mt-0.5" />
                                    <div>
                                        <p className="font-semibold text-white">Dirección:</p>
                                        <p className="opacity-90">{club.club_address} {club.club_city ? `(${club.club_city})` : ''}</p>
                                    </div>
                                </div>
                            )}
                            <div className="flex items-start gap-2">
                                <Clock className="h-4 w-4 shrink-0 text-emerald-300 mt-0.5" />
                                <div>
                                    <p className="font-semibold text-white">Horarios de Atención:</p>
                                    <p className="opacity-90">{club.club_schedule}</p>
                                </div>
                            </div>
                            {club.club_amenities && club.club_amenities.length > 0 && (
                                <div className="flex items-start gap-2 sm:col-span-2 md:col-span-1">
                                    <Sparkles className="h-4 w-4 shrink-0 text-emerald-300 mt-0.5" />
                                    <div>
                                        <p className="font-semibold text-white">Servicios en el Club:</p>
                                        <div className="flex flex-wrap gap-1 mt-1">
                                            {club.club_amenities.map((a, i) => (
                                                <span key={i} className="inline-block rounded-md bg-white/15 px-1.5 py-0.5 text-[10px] font-medium">
                                                    {a}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </section>

                {/* Search & Category Filter Section */}
                <section className="space-y-4">
                    <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
                        <div className="relative flex-1 max-w-md">
                            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                            <Input
                                placeholder="Buscar waffles, batidos, mega tés..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="pl-10 rounded-2xl bg-muted/40 border-border/60 h-11 text-xs sm:text-sm"
                            />
                            {searchQuery && (
                                <button
                                    onClick={() => setSearchQuery('')}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                                >
                                    <X className="h-4 w-4" />
                                </button>
                            )}
                        </div>
                    </div>

                    {/* Category Tabs */}
                    <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
                        {categories.map((cat) => {
                            const isSelected = selectedCategory === cat.id;
                            return (
                                <button
                                    key={cat.id}
                                    onClick={() => setSelectedCategory(cat.id)}
                                    className={cn(
                                        'flex items-center gap-1.5 rounded-2xl px-4 py-2.5 text-xs font-bold whitespace-nowrap transition-all duration-200 border shrink-0',
                                        isSelected
                                            ? 'bg-emerald-600 text-white border-emerald-600 shadow-md shadow-emerald-600/20'
                                            : 'bg-muted/40 hover:bg-muted/70 text-muted-foreground border-border/50 hover:text-foreground'
                                    )}
                                >
                                    <span>{cat.icon}</span>
                                    <span>{cat.label}</span>
                                </button>
                            );
                        })}
                    </div>
                </section>

                {/* Product Catalog Grid */}
                <section className="space-y-4">
                    {filteredProducts.length === 0 ? (
                        <div className="rounded-3xl border border-dashed border-border/80 p-12 text-center space-y-3">
                            <UtensilsCrossed className="mx-auto h-10 w-10 text-muted-foreground/60" />
                            <p className="font-bold text-sm text-foreground">No encontramos preparaciones en esta categoría</p>
                            <p className="text-xs text-muted-foreground">Prueba seleccionando otra categoría o limpiando la búsqueda.</p>
                            <Button variant="outline" size="sm" onClick={() => { setSelectedCategory('all'); setSearchQuery(''); }} className="rounded-xl text-xs">
                                Ver todo el menú
                            </Button>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
                            {filteredProducts.map((product) => (
                                <Card
                                    key={product.id}
                                    className="group rounded-3xl border border-border/60 overflow-hidden bg-card/60 backdrop-blur-sm shadow-md hover:shadow-xl transition-all duration-300 flex flex-col justify-between"
                                >
                                    <div>
                                        {/* Product Image */}
                                        <div className="relative h-48 w-full overflow-hidden bg-muted">
                                            {product.image_url ? (
                                                <img
                                                    src={product.image_url}
                                                    alt={product.name}
                                                    className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                                                />
                                            ) : (
                                                <div className="h-full w-full flex items-center justify-center bg-gradient-to-tr from-emerald-500/10 to-teal-500/10 text-4xl">
                                                    🥤
                                                </div>
                                            )}
                                            <div className="absolute top-3 left-3 flex flex-wrap gap-1">
                                                {product.protein_grams && product.protein_grams > 0 && (
                                                    <Badge className="bg-emerald-600/90 hover:bg-emerald-600 text-white font-bold text-[10px] backdrop-blur-md border-none shadow-sm">
                                                        <Zap className="w-2.5 h-2.5 mr-0.5" />
                                                        {product.protein_grams}g Proteína
                                                    </Badge>
                                                )}
                                                {product.calories && (
                                                    <Badge variant="secondary" className="bg-black/60 text-white font-bold text-[10px] backdrop-blur-md border-none">
                                                        <Flame className="w-2.5 h-2.5 mr-0.5 text-amber-400" />
                                                        {product.calories} kcal
                                                    </Badge>
                                                )}
                                            </div>
                                        </div>

                                        {/* Content */}
                                        <CardContent className="p-5 space-y-2">
                                            <div className="flex items-start justify-between gap-2">
                                                <h3 className="font-extrabold text-base text-foreground leading-snug group-hover:text-emerald-600 transition-colors">
                                                    {product.name}
                                                </h3>
                                                <span className="font-black text-emerald-600 dark:text-emerald-400 text-base shrink-0">
                                                    ${product.price.toFixed(2)}
                                                </span>
                                            </div>
                                            <p className="text-xs text-muted-foreground leading-relaxed line-clamp-2">
                                                {product.description}
                                            </p>

                                            {/* Benefits Pill tags */}
                                            {product.benefits && product.benefits.length > 0 && (
                                                <div className="flex flex-wrap gap-1 pt-1">
                                                    {product.benefits.slice(0, 2).map((b, idx) => (
                                                        <span key={idx} className="rounded-md bg-muted/80 text-foreground/80 px-2 py-0.5 text-[10px] font-semibold">
                                                            ✓ {b}
                                                        </span>
                                                    ))}
                                                </div>
                                            )}
                                        </CardContent>
                                    </div>

                                    {/* Action Button */}
                                    <div className="p-5 pt-0">
                                        <Button
                                            onClick={() => handleOpenCustomize(product)}
                                            className="w-full rounded-2xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs h-10 shadow-md shadow-emerald-600/15 gap-2"
                                        >
                                            <Plus className="w-4 h-4" />
                                            <span>Personalizar & Pedir</span>
                                        </Button>
                                    </div>
                                </Card>
                            ))}
                        </div>
                    )}
                </section>
            </main>

            {/* Floating Cart Button (Mobile sticky bottom) */}
            {cartCount > 0 && (
                <div className="fixed bottom-6 inset-x-4 max-w-lg mx-auto z-40">
                    <Button
                        size="lg"
                        onClick={() => setIsCartOpen(true)}
                        className="w-full rounded-3xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-black text-sm h-14 shadow-2xl shadow-emerald-600/30 flex items-center justify-between px-6"
                    >
                        <div className="flex items-center gap-2">
                            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-white text-emerald-700 text-xs font-black">
                                {cartCount}
                            </span>
                            <span>Ver mi Pedido</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-base font-black">${cartSubtotal.toFixed(2)}</span>
                            <ChevronRight className="h-5 w-5" />
                        </div>
                    </Button>
                </div>
            )}

            {/* ══════════════════════════════════════════════════════════════════
                CUSTOMIZATION MODAL
            ══════════════════════════════════════════════════════════════════ */}
            <Dialog open={Boolean(activeProduct)} onOpenChange={(open) => !open && setActiveProduct(null)}>
                <DialogContent className="rounded-3xl max-w-md p-6 max-h-[90vh] overflow-y-auto">
                    {activeProduct && (
                        <div className="space-y-6">
                            <DialogHeader>
                                <DialogTitle className="text-xl font-black text-foreground">
                                    {activeProduct.name}
                                </DialogTitle>
                                <DialogDescription className="text-xs text-muted-foreground leading-relaxed pt-1">
                                    {activeProduct.description}
                                </DialogDescription>
                            </DialogHeader>

                            {/* Flavor Choice */}
                            {activeProduct.customization_options?.flavors && activeProduct.customization_options.flavors.length > 0 && (
                                <div className="space-y-2.5">
                                    <Label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                                        1. Elige tu Sabor Favorito *
                                    </Label>
                                    <div className="grid grid-cols-2 gap-2">
                                        {activeProduct.customization_options.flavors.map((fl) => (
                                            <button
                                                key={fl}
                                                type="button"
                                                onClick={() => setModalFlavor(fl)}
                                                className={cn(
                                                    'p-3 rounded-2xl border text-xs font-bold text-left transition-all',
                                                    modalFlavor === fl
                                                        ? 'bg-emerald-600 text-white border-emerald-600 shadow-md shadow-emerald-600/20'
                                                        : 'bg-muted/40 border-border/60 hover:bg-muted/70 text-foreground'
                                                )}
                                            >
                                                {fl}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Temperature Option */}
                            {activeProduct.customization_options?.temperature && activeProduct.customization_options.temperature.length > 0 && (
                                <div className="space-y-2.5">
                                    <Label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                                        2. Temperatura / Preparación
                                    </Label>
                                    <div className="grid grid-cols-2 gap-2">
                                        {activeProduct.customization_options.temperature.map((temp) => (
                                            <button
                                                key={temp}
                                                type="button"
                                                onClick={() => setModalTemperature(temp)}
                                                className={cn(
                                                    'p-3 rounded-2xl border text-xs font-bold text-left transition-all',
                                                    modalTemperature === temp
                                                        ? 'bg-emerald-600 text-white border-emerald-600 shadow-md shadow-emerald-600/20'
                                                        : 'bg-muted/40 border-border/60 hover:bg-muted/70 text-foreground'
                                                )}
                                            >
                                                {temp}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Topping Choice */}
                            {activeProduct.customization_options?.toppings && activeProduct.customization_options.toppings.length > 0 && (
                                <div className="space-y-2.5">
                                    <Label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                                        3. Toppings & Agregados (Opcional)
                                    </Label>
                                    <div className="flex flex-wrap gap-2">
                                        {activeProduct.customization_options.toppings.map((tp) => {
                                            const isSelected = modalToppings.includes(tp);
                                            return (
                                                <button
                                                    key={tp}
                                                    type="button"
                                                    onClick={() => toggleTopping(tp)}
                                                    className={cn(
                                                        'px-3.5 py-2 rounded-xl border text-xs font-semibold transition-all',
                                                        isSelected
                                                            ? 'bg-teal-600 text-white border-teal-600 shadow-sm'
                                                            : 'bg-muted/30 border-border/50 hover:bg-muted/60 text-muted-foreground'
                                                    )}
                                                >
                                                    {isSelected ? '✓ ' : '+ '}
                                                    {tp}
                                                </button>
                                            );
                                        })}
                                    </div>
                                </div>
                            )}

                            {/* Special instructions */}
                            <div className="space-y-2">
                                <Label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                                    Instrucciones Especiales (Opcional)
                                </Label>
                                <Input
                                    placeholder="Ej: Sin azúcar, poco hielo, extra canela..."
                                    value={modalNotes}
                                    onChange={(e) => setModalNotes(e.target.value)}
                                    className="rounded-2xl text-xs bg-muted/30 h-10"
                                />
                            </div>

                            {/* Quantity & Add Action */}
                            <div className="pt-2 flex items-center justify-between gap-4">
                                <div className="flex items-center gap-3 rounded-2xl border border-border/60 bg-muted/40 p-1.5">
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        onClick={() => setModalQuantity(Math.max(1, modalQuantity - 1))}
                                        className="h-8 w-8 rounded-xl"
                                    >
                                        <Minus className="h-3.5 w-3.5" />
                                    </Button>
                                    <span className="font-extrabold text-sm w-4 text-center">{modalQuantity}</span>
                                    <Button
                                        variant="ghost"
                                        size="icon"
                                        onClick={() => setModalQuantity(modalQuantity + 1)}
                                        className="h-8 w-8 rounded-xl"
                                    >
                                        <Plus className="h-3.5 w-3.5" />
                                    </Button>
                                </div>

                                <Button
                                    onClick={handleAddToCart}
                                    className="flex-1 rounded-2xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs h-11 shadow-lg shadow-emerald-600/20"
                                >
                                    Agregar al Pedido • ${(activeProduct.price * modalQuantity).toFixed(2)}
                                </Button>
                            </div>
                        </div>
                    )}
                </DialogContent>
            </Dialog>

            {/* ══════════════════════════════════════════════════════════════════
                CART & CHECKOUT DRAWER
            ══════════════════════════════════════════════════════════════════ */}
            <Sheet open={isCartOpen} onOpenChange={setIsCartOpen}>
                <SheetContent side="right" className="w-full sm:max-w-md p-6 flex flex-col justify-between overflow-y-auto">
                    <div className="space-y-6">
                        <SheetHeader>
                            <SheetTitle className="text-xl font-black flex items-center gap-2">
                                <ShoppingBag className="w-5 h-5 text-emerald-600" />
                                Tu Pedido ({cartCount})
                            </SheetTitle>
                            <SheetDescription className="text-xs text-muted-foreground">
                                Revisa tus preparaciones y confirma tu orden para enviarla directo a WhatsApp.
                            </SheetDescription>
                        </SheetHeader>

                        {/* Order Items List */}
                        <div className="space-y-3 divide-y divide-border/40">
                            {cart.map((item) => (
                                <div key={item.cart_item_id} className="pt-3 first:pt-0 flex items-start justify-between gap-3">
                                    <div className="space-y-1 text-xs">
                                        <p className="font-extrabold text-foreground">{item.name}</p>
                                        {item.flavor && <p className="text-muted-foreground">• Sabor: <span className="font-medium text-foreground">{item.flavor}</span></p>}
                                        {item.toppings.length > 0 && <p className="text-muted-foreground">• Toppings: <span className="font-medium text-foreground">{item.toppings.join(', ')}</span></p>}
                                        {item.temperature && <p className="text-muted-foreground">• Temp: <span className="font-medium text-foreground">{item.temperature}</span></p>}
                                        {item.notes && <p className="text-muted-foreground italic">• "{item.notes}"</p>}
                                        <p className="font-black text-emerald-600 dark:text-emerald-400 pt-0.5">${item.total.toFixed(2)}</p>
                                    </div>

                                    <div className="flex items-center gap-2">
                                        <div className="flex items-center gap-1.5 rounded-xl border bg-muted/30 p-1">
                                            <button
                                                onClick={() => handleUpdateCartQty(item.cart_item_id, -1)}
                                                className="h-6 w-6 rounded-lg flex items-center justify-center hover:bg-muted font-bold text-xs"
                                            >
                                                -
                                            </button>
                                            <span className="text-xs font-bold px-1">{item.quantity}</span>
                                            <button
                                                onClick={() => handleUpdateCartQty(item.cart_item_id, 1)}
                                                className="h-6 w-6 rounded-lg flex items-center justify-center hover:bg-muted font-bold text-xs"
                                            >
                                                +
                                            </button>
                                        </div>
                                        <button
                                            onClick={() => handleRemoveFromCart(item.cart_item_id)}
                                            className="text-muted-foreground hover:text-destructive p-1"
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>

                        {/* Delivery Option Selector */}
                        <div className="space-y-3 pt-2">
                            <Label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                                Modalidad de Entrega *
                            </Label>
                            <RadioGroup value={deliveryType} onValueChange={setDeliveryType} className="grid grid-cols-3 gap-2">
                                <div>
                                    <RadioGroupItem value="dine_in" id="del_dine" className="peer sr-only" />
                                    <Label
                                        htmlFor="del_dine"
                                        className="flex flex-col items-center justify-between rounded-2xl border-2 border-muted bg-popover p-3 hover:bg-accent hover:text-accent-foreground peer-data-[state=checked]:border-emerald-600 peer-data-[state=checked]:bg-emerald-500/10 text-center cursor-pointer text-xs"
                                    >
                                        <span className="text-lg">🍽️</span>
                                        <span className="font-bold mt-1">En el Club</span>
                                    </Label>
                                </div>
                                <div>
                                    <RadioGroupItem value="pickup" id="del_pickup" className="peer sr-only" />
                                    <Label
                                        htmlFor="del_pickup"
                                        className="flex flex-col items-center justify-between rounded-2xl border-2 border-muted bg-popover p-3 hover:bg-accent hover:text-accent-foreground peer-data-[state=checked]:border-emerald-600 peer-data-[state=checked]:bg-emerald-500/10 text-center cursor-pointer text-xs"
                                    >
                                        <span className="text-lg">🥡</span>
                                        <span className="font-bold mt-1">Para Llevar</span>
                                    </Label>
                                </div>
                                <div>
                                    <RadioGroupItem value="delivery" id="del_deliv" className="peer sr-only" />
                                    <Label
                                        htmlFor="del_deliv"
                                        className="flex flex-col items-center justify-between rounded-2xl border-2 border-muted bg-popover p-3 hover:bg-accent hover:text-accent-foreground peer-data-[state=checked]:border-emerald-600 peer-data-[state=checked]:bg-emerald-500/10 text-center cursor-pointer text-xs"
                                    >
                                        <span className="text-lg">🛵</span>
                                        <span className="font-bold mt-1">A Domicilio</span>
                                    </Label>
                                </div>
                            </RadioGroup>
                        </div>

                        {/* Customer Information Form */}
                        <div className="space-y-3">
                            <Label className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                                Tus Datos de Contacto
                            </Label>
                            <Input
                                placeholder="Tu Nombre y Apellido *"
                                value={customerName}
                                onChange={(e) => setCustomerName(e.target.value)}
                                className="rounded-2xl text-xs bg-muted/40 h-10"
                            />
                            <Input
                                placeholder="Tu Número de WhatsApp (Opcional)"
                                value={customerPhone}
                                onChange={(e) => setCustomerPhone(e.target.value)}
                                className="rounded-2xl text-xs bg-muted/40 h-10"
                            />
                            <Textarea
                                placeholder="Notas adicionales o dirección si es a domicilio..."
                                value={orderNotes}
                                onChange={(e) => setOrderNotes(e.target.value)}
                                className="rounded-2xl text-xs bg-muted/40 resize-none h-16"
                            />
                        </div>
                    </div>

                    {/* Drawer Footer & Checkout Button */}
                    <div className="pt-6 space-y-3 border-t border-border/60">
                        <div className="flex items-center justify-between text-sm">
                            <span className="text-muted-foreground font-semibold">Total a Pagar:</span>
                            <span className="text-xl font-black text-emerald-600 dark:text-emerald-400">
                                ${cartSubtotal.toFixed(2)} USD
                            </span>
                        </div>

                        <Button
                            onClick={() => orderMutation.mutate()}
                            disabled={!customerName.trim() || cart.length === 0 || orderMutation.isPending}
                            className="w-full rounded-2xl bg-emerald-600 hover:bg-emerald-700 text-white font-black text-sm h-12 shadow-xl shadow-emerald-600/20 gap-2"
                        >
                            {orderMutation.isPending ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                                <MessageCircle className="h-4 w-4" />
                            )}
                            <span>Confirmar y Pedir por WhatsApp</span>
                        </Button>
                    </div>
                </SheetContent>
            </Sheet>

            {/* ══════════════════════════════════════════════════════════════════
                ORDER CONFIRMATION DIALOG
            ══════════════════════════════════════════════════════════════════ */}
            <Dialog open={Boolean(orderSuccessData)} onOpenChange={(open) => !open && setOrderSuccessData(null)}>
                <DialogContent className="rounded-3xl max-w-md p-6 text-center space-y-4">
                    <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 shadow-inner">
                        <CheckCircle2 className="h-8 w-8" />
                    </div>
                    <div className="space-y-1">
                        <DialogTitle className="text-xl font-black">
                            ¡Pedido Registrado con Éxito!
                        </DialogTitle>
                        <p className="text-xs text-muted-foreground">
                            Orden #{orderSuccessData?.orderNumber} creada para el Club de Nutrición.
                        </p>
                    </div>
                    <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-950 dark:text-emerald-300 text-left space-y-1.5">
                        <p className="font-bold">📱 Siguiente paso:</p>
                        <p className="leading-relaxed">
                            Si no se abrió automáticamente tu WhatsApp, haz clic en el botón inferior para enviar el detalle de tu orden directamente al Coach del Club.
                        </p>
                    </div>
                    <DialogFooter className="flex-col gap-2 pt-2">
                        {orderSuccessData?.whatsappUrl && (
                            <Button
                                onClick={() => window.open(orderSuccessData.whatsappUrl, '_blank')}
                                className="w-full rounded-2xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs h-11 shadow-lg shadow-emerald-600/20 gap-2"
                            >
                                <MessageCircle className="h-4 w-4" />
                                <span>Abrir WhatsApp del Club</span>
                            </Button>
                        )}
                        <Button
                            variant="outline"
                            onClick={() => setOrderSuccessData(null)}
                            className="w-full rounded-2xl text-xs font-semibold"
                        >
                            Cerrar
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
