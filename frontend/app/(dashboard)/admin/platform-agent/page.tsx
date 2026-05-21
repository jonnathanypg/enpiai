'use client';

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import Cookies from 'js-cookie';
import { useRouter } from 'next/navigation';
import { Bot, Save, Loader2, MessageSquare, Zap, Shield, Globe, FileText } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import apiClient from '@/lib/api-client';

export default function PlatformAgentPage() {
    const { t } = useTranslation();
    const router = useRouter();
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [data, setData] = useState<any>(null);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const response = await apiClient.get('/admin/platform-agent');
            setData(response.data.data);
        } catch (error) {
            console.error('Error fetching platform agent:', error);
            toast.error(t('adminPlatformAgent.loadError') || 'Error al cargar configuración');
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        try {
            setSaving(true);
            
            // If data is null, we're doing the initial setup.
            // We can send an empty object or just the defaults.
            const payload = data ? {
                distributor: {
                    name: data.distributor.name,
                    agent_name: data.distributor.agent_name,
                    llm_model: data.distributor.llm_model,
                },
                agent: {
                    name: data.agent.name,
                    tone: data.agent.tone,
                    objective: data.agent.objective,
                    system_prompt: data.agent.system_prompt,
                    features: data.agent.features
                }
            } : {};

            await apiClient.post('/admin/platform-agent', payload);
            toast.success(t('adminPlatformAgent.saveSuccess'));
            
            // Refresh data after save/init
            fetchData();
        } catch (error) {
            console.error('Error saving platform agent:', error);
            toast.error(t('adminPlatformAgent.saveError'));
        } finally {
            setSaving(false);
        }
    };

    const toggleFeature = (name: string) => {
        const updatedFeatures = data.agent.features.map((f: any) => 
            f.name === name ? { ...f, is_enabled: !f.is_enabled } : f
        );
        setData({
            ...data,
            agent: { ...data.agent, features: updatedFeatures }
        });
    };

    const manageAssets = (path: string) => {
        // Set the override cookie so standard pages manage THIS distributor
        Cookies.set('distributor_id_override', data.distributor.id.toString(), { expires: 1 });
        router.push(path);
    };

    if (loading) {
        return (
            <div className="flex h-[60vh] items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                <span className="ml-2 text-muted-foreground">{t('adminPlatformAgent.loading')}</span>
            </div>
        );
    }

    // Initialize data if null (after setup)
    if (!data) {
        return (
            <div className="flex flex-col items-center justify-center h-[60vh] gap-4">
                <Bot className="h-16 w-16 text-muted-foreground/20" />
                <div className="text-center">
                    <h3 className="text-lg font-semibold">Plataforma no inicializada</h3>
                    <p className="text-muted-foreground mb-4">Haz clic abajo para crear el registro del agente oficial.</p>
                    <Button onClick={() => handleSave()}>Inicializar Agente Enpi</Button>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-5xl mx-auto space-y-8 animate-slow-fade">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                        {t('adminPlatformAgent.title')}
                    </h1>
                    <p className="text-muted-foreground">
                        {t('adminPlatformAgent.description')}
                    </p>
                </div>
                <Button onClick={handleSave} disabled={saving} className="vivid-gradient shadow-lg">
                    {saving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Save className="mr-2 h-4 w-4" />}
                    {t('common.save')}
                </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Profile Card */}
                <Card className="md:col-span-2 glass-card">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Bot className="h-5 w-5 text-primary" />
                            {t('adminPlatformAgent.agentTitle')}
                        </CardTitle>
                        <CardDescription>Configura la identidad y comportamiento del agente de soporte oficial.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="platform-name">{t('adminPlatformAgent.platformName')}</Label>
                                <Input 
                                    id="platform-name" 
                                    value={data.distributor.name} 
                                    onChange={(e) => setData({...data, distributor: {...data.distributor, name: e.target.value}})}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="agent-name">{t('adminPlatformAgent.agentName')}</Label>
                                <Input 
                                    id="agent-name" 
                                    value={data.distributor.agent_name} 
                                    onChange={(e) => setData({...data, distributor: {...data.distributor, agent_name: e.target.value}})}
                                />
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="tone">{t('adminPlatformAgent.agentTone')}</Label>
                                <Select 
                                    value={data.agent.tone} 
                                    onValueChange={(val) => setData({...data, agent: {...data.agent, tone: val}})}
                                >
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="friendly">Amigable</SelectItem>
                                        <SelectItem value="professional">Profesional</SelectItem>
                                        <SelectItem value="sales">Ventas (Persuasivo)</SelectItem>
                                        <SelectItem value="support">Soporte</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="objective">{t('adminPlatformAgent.agentObjective')}</Label>
                                <Select 
                                    value={data.agent.objective} 
                                    onValueChange={(val) => setData({...data, agent: {...data.agent, objective: val}})}
                                >
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="sales">Vender Suscripciones</SelectItem>
                                        <SelectItem value="lead_qualification">Calificar Distribuidores</SelectItem>
                                        <SelectItem value="customer_service">Atención al Cliente</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <div className="flex items-center justify-between">
                                <Label htmlFor="system-prompt">{t('adminPlatformAgent.systemPrompt')}</Label>
                                <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest bg-primary/10 px-2 py-0.5 rounded">Core Logic</span>
                            </div>
                            <Textarea 
                                id="system-prompt" 
                                rows={6}
                                placeholder={t('adminPlatformAgent.systemPromptPlaceholder')}
                                value={data.agent.system_prompt || ''} 
                                onChange={(e) => setData({...data, agent: {...data.agent, system_prompt: e.target.value}})}
                                className="bg-white/5 border-white/10 italic"
                            />
                            <p className="text-xs text-muted-foreground italic">Este prompt define la estrategia de venta y el "FOMO" que mencionaste.</p>
                        </div>
                    </CardContent>
                </Card>

                {/* Features & Stats */}
                <div className="space-y-6">
                    <Card className="glass-card border-primary/20">
                        <CardHeader className="pb-3">
                            <CardTitle className="text-sm flex items-center gap-2">
                                <Zap className="h-4 w-4 text-secondary" />
                                {t('adminPlatformAgent.features')}
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {data.agent.features.filter((f: any) => f.category === 'channel' || f.category === 'skill').map((feat: any) => (
                                <div key={feat.name} className="flex items-center justify-between">
                                    <div className="flex flex-col">
                                        <span className="text-sm font-medium">{feat.label}</span>
                                        <span className="text-[10px] text-muted-foreground">{feat.category}</span>
                                    </div>
                                    <Switch 
                                        checked={feat.is_enabled} 
                                        onCheckedChange={() => toggleFeature(feat.name)}
                                    />
                                </div>
                            ))}
                        </CardContent>
                    </Card>

                    <Card className="glass-card bg-primary/5 border-dashed">
                        <CardHeader className="pb-3">
                            <CardTitle className="text-sm flex items-center gap-2">
                                <Shield className="h-4 w-4 text-primary" />
                                Global Knowledge
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="text-xs text-muted-foreground">
                            El Agente Enpi tiene acceso automático a la base de conocimientos global y a sus propios documentos privados cargados en la sección de documentos de este perfil.
                        </CardContent>
                        <CardFooter className="flex flex-col gap-2">
                            <Button variant="outline" size="sm" className="w-full text-[10px] justify-start" onClick={() => manageAssets('/channels')}>
                                <Globe className="mr-2 h-3 w-3 text-primary" />
                                Configurar WhatsApp/Telegram Enpi
                            </Button>
                            <Button variant="outline" size="sm" className="w-full text-[10px] justify-start" onClick={() => manageAssets('/documents')}>
                                <FileText className="mr-2 h-3 w-3 text-secondary" />
                                Gestionar Documentos Enpi
                            </Button>
                            <Button variant="outline" size="sm" className="w-full text-[10px] justify-start" asChild>
                                <a href="/admin/documents">
                                    <Shield className="mr-2 h-3 w-3 text-muted-foreground" />
                                    Base de Conocimiento Global
                                </a>
                            </Button>
                        </CardFooter>
                    </Card>
                </div>
            </div>
            
            <div className="bg-gradient-to-r from-primary/10 to-secondary/10 p-6 rounded-2xl border border-white/10 flex items-center gap-6">
                 <div className="h-12 w-12 rounded-full bg-white flex items-center justify-center shadow-lg">
                    <Globe className="h-6 w-6 text-primary animate-pulse" />
                 </div>
                 <div>
                    <h4 className="font-bold text-lg">Integración Multicanal Activa</h4>
                    <p className="text-sm text-muted-foreground">Recuerda configurar los tokens de WhatsApp y Telegram en la sección de <strong>Canales</strong> del perfil del Agente Enpi para que pueda responder externamente.</p>
                 </div>
            </div>
        </div>
    );
}
