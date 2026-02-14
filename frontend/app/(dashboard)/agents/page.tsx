'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Bot, Save, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { Textarea } from '@/components/ui/textarea';
import apiClient from '@/lib/api-client';

interface AgentPersona {
    agent_name: string | null;
    personality_prompt: string | null;
}

export default function AgentSetupPage() {
    const queryClient = useQueryClient();

    const { data: settings, isLoading } = useQuery({
        queryKey: ['distributor-settings'],
        queryFn: async () => {
            const { data } = await apiClient.get<{ data: AgentPersona }>('/distributors/settings');
            return data.data;
        },
    });

    const [agentName, setAgentName] = useState('');
    const [persona, setPersona] = useState('');

    useEffect(() => {
        if (settings) {
            setAgentName(settings.agent_name || '');
            setPersona(settings.personality_prompt || '');
        }
    }, [settings]);

    const saveMutation = useMutation({
        mutationFn: async () => {
            const { data } = await apiClient.put('/distributors/agent-persona', {
                agent_name: agentName,
                personality_prompt: persona,
            });
            return data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['distributor-settings'] });
            toast.success('Agent updated successfully.');
        },
        onError: (error: unknown) => {
            const message =
                (error as { response?: { data?: { error?: string } } })?.response?.data?.error ||
                'Failed to save';
            toast.error(message);
        },
    });

    if (isLoading) {
        return (
            <div className="mx-auto max-w-2xl space-y-6">
                <Skeleton className="h-10 w-48" />
                <Skeleton className="h-64 w-full" />
            </div>
        );
    }

    return (
        <div className="mx-auto max-w-2xl space-y-8">
            <div>
                <h2 className="flex items-center gap-2 text-3xl font-bold tracking-tight">
                    <Bot className="h-7 w-7 text-primary" />
                    Agent Setup
                </h2>
                <p className="text-muted-foreground">
                    Personalize your AI assistant. These settings define how the agent
                    introduces itself and behaves in conversations with your leads.
                </p>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Assistant Profile</CardTitle>
                    <CardDescription>
                        Give your agent a name and personality. Both fields are optional —
                        the agent works perfectly with default settings.
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    <div className="space-y-2">
                        <Label htmlFor="agent_name">Agent Name</Label>
                        <Input
                            id="agent_name"
                            placeholder="e.g. Luna, Max, Asistente"
                            value={agentName}
                            onChange={(e) => setAgentName(e.target.value)}
                        />
                        <p className="text-xs text-muted-foreground">
                            The name your agent will use when greeting customers.
                            Leave blank for the default &quot;Asistente&quot;.
                        </p>
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="persona">
                            Personality / Custom Instructions{' '}
                            <span className="text-muted-foreground">(optional)</span>
                        </Label>
                        <Textarea
                            id="persona"
                            placeholder="e.g. You are a friendly wellness coach who specializes in nutrition. Always greet users warmly and ask about their health goals."
                            value={persona}
                            onChange={(e) => setPersona(e.target.value)}
                            rows={5}
                        />
                        <p className="text-xs text-muted-foreground">
                            Describe how you want the agent to behave. If left empty, the
                            agent will use a professional, friendly default style.
                        </p>
                    </div>

                    <Button
                        onClick={() => saveMutation.mutate()}
                        disabled={saveMutation.isPending}
                        className="w-full"
                    >
                        {saveMutation.isPending ? (
                            <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Saving...
                            </>
                        ) : (
                            <>
                                <Save className="mr-2 h-4 w-4" />
                                Save Changes
                            </>
                        )}
                    </Button>
                </CardContent>
            </Card>
        </div>
    );
}
