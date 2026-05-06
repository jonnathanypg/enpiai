'use client';

import { useState, useRef, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Send, Bot, User, Loader2, Trash2, Sparkles } from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from 'sonner';
import apiClient from '@/lib/api-client';
import { cn } from '@/lib/utils';

interface ChatMessage {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
}

import { useTranslation } from 'react-i18next';

export default function PlaygroundPage() {
    const { t } = useTranslation();
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const scrollRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    // Auto-scroll to bottom on new messages
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const chatMutation = useMutation({
        mutationFn: async (userMessage: string) => {
            // Build OpenAI-compatible messages array
            const chatMessages = [
                ...messages.map((m) => ({ role: m.role, content: m.content })),
                { role: 'user' as const, content: userMessage },
            ];

            const { data } = await apiClient.post('/agents/chat', {
                messages: chatMessages,
                user: 'playground_user',
            });
            return data;
        },
        onSuccess: (data) => {
            const assistantContent =
                data?.choices?.[0]?.message?.content ||
                data?.data?.content ||
                data?.content ||
                t('playground.noResponse', { defaultValue: 'No response received.' });

            const assistantMsg: ChatMessage = {
                id: `assistant-${Date.now()}`,
                role: 'assistant',
                content: assistantContent,
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, assistantMsg]);
        },
        onError: (error: unknown) => {
            const message =
                (error as { response?: { data?: { error?: { message?: string }; error_message?: string } } })
                    ?.response?.data?.error?.message ||
                (error as { response?: { data?: { error_message?: string } } })?.response?.data?.error_message ||
                t('common.error', { defaultValue: 'Failed to get response' });
            toast.error(message);
        },
    });

    const handleSend = () => {
        const trimmed = input.trim();
        if (!trimmed || chatMutation.isPending) return;

        const userMsg: ChatMessage = {
            id: `user-${Date.now()}`,
            role: 'user',
            content: trimmed,
            timestamp: new Date(),
        };

        setMessages((prev) => [...prev, userMsg]);
        setInput('');
        chatMutation.mutate(trimmed);
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const clearChat = () => {
        setMessages([]);
        toast.info(t('playground.clearSuccess', { defaultValue: 'Conversation reset.' }));
    };

    return (
        <div className="flex h-[calc(100vh-8rem)] flex-col">
            {/* Header */}
            <div className="mb-4 flex items-center justify-between">
                <div>
                    <h2 className="flex items-center gap-2 text-3xl font-bold tracking-tight">
                        <Sparkles className="h-7 w-7 text-primary" />
                        {t('playground.title')}
                    </h2>
                    <p className="text-muted-foreground">
                        {t('playground.description')}
                    </p>
                </div>
                <Button variant="outline" size="sm" onClick={clearChat} disabled={messages.length === 0}>
                    <Trash2 className="mr-2 h-4 w-4" />
                    {t('playground.clearChat')}
                </Button>
            </div>

            {/* Chat Area */}
            <Card className="flex flex-1 flex-col overflow-hidden">
                <CardHeader className="border-b px-6 py-3">
                    <CardTitle className="flex items-center gap-2 text-sm font-medium">
                        <Bot className="h-4 w-4 text-primary" />
                        {t('playground.liveAgentChat')}
                        {chatMutation.isPending && (
                            <span className="flex items-center gap-1 text-xs text-muted-foreground">
                                <Loader2 className="h-3 w-3 animate-spin" />
                                {t('common.saving', { defaultValue: 'Thinking...' })}
                            </span>
                        )}
                    </CardTitle>
                </CardHeader>

                {/* Messages */}
                <CardContent ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto p-4">
                    {messages.length === 0 ? (
                        <div className="flex h-full flex-col items-center justify-center text-center text-muted-foreground">
                            <Bot className="mb-4 h-16 w-16 opacity-20" />
                            <p className="text-lg font-medium">{t('common.noResults', { defaultValue: 'No messages yet' })}</p>
                            <p className="text-sm">
                                {t('playground.startTesting')}
                            </p>
                        </div>
                    ) : (
                        messages.map((msg) => (
                            <div
                                key={msg.id}
                                className={cn(
                                    'flex gap-3',
                                    msg.role === 'user' ? 'justify-end' : 'justify-start'
                                )}
                            >
                                {msg.role === 'assistant' && (
                                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10">
                                        <Bot className="h-4 w-4 text-primary" />
                                    </div>
                                )}
                                <div
                                    className={cn(
                                        'max-w-[75%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed',
                                        msg.role === 'user'
                                            ? 'bg-primary text-primary-foreground'
                                            : 'bg-muted'
                                    )}
                                >
                                    <p className="whitespace-pre-wrap">{msg.content}</p>
                                    <p
                                        className={cn(
                                            'mt-1 text-[10px]',
                                            msg.role === 'user'
                                                ? 'text-primary-foreground/60'
                                                : 'text-muted-foreground'
                                        )}
                                    >
                                        {msg.timestamp.toLocaleTimeString([], {
                                            hour: '2-digit',
                                            minute: '2-digit',
                                        })}
                                    </p>
                                </div>
                                {msg.role === 'user' && (
                                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-accent">
                                        <User className="h-4 w-4" />
                                    </div>
                                )}
                            </div>
                        ))
                    )}

                    {/* Typing indicator */}
                    {chatMutation.isPending && (
                        <div className="flex gap-3">
                            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10">
                                <Bot className="h-4 w-4 text-primary" />
                            </div>
                            <div className="rounded-2xl bg-muted px-4 py-3">
                                <div className="flex gap-1">
                                    <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/40 [animation-delay:0ms]" />
                                    <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/40 [animation-delay:150ms]" />
                                    <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/40 [animation-delay:300ms]" />
                                </div>
                            </div>
                        </div>
                    )}
                </CardContent>

                {/* Input */}
                <div className="border-t p-4">
                    <div className="flex gap-2">
                        <Input
                            ref={inputRef}
                            placeholder={t('playground.typeMessage')}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            disabled={chatMutation.isPending}
                            className="flex-1"
                        />
                        <Button
                            onClick={handleSend}
                            disabled={!input.trim() || chatMutation.isPending}
                            size="icon"
                        >
                            {chatMutation.isPending ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                                <Send className="h-4 w-4" />
                            )}
                        </Button>
                    </div>
                    <p className="mt-2 text-xs text-muted-foreground">
                        {t('playground.helpText')}
                    </p>
                </div>
            </Card>
        </div>
    );
}
