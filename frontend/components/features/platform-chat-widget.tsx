'use client';

import { useState, useEffect, useRef } from 'react';
import { MessageCircle, X, Send, Loader2, Bot, Mic, Square, Volume2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import apiClient from '@/lib/api-client';

export function PlatformChatWidget() {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState<{role: 'user' | 'assistant', content: string}[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [conversationId, setConversationId] = useState<number | null>(null);
    const [isRecording, setIsRecording] = useState(false);
    const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
    
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const unlockAudio = () => {
        if (typeof window !== 'undefined') {
            const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
            if (AudioContext) {
                const ctx = new AudioContext();
                if (ctx.state === 'suspended') {
                    ctx.resume();
                }
            }
        }
    };

    const handleOpen = () => {
        setIsOpen(!isOpen);
        unlockAudio();
        if (messages.length === 0) {
            setMessages([{role: 'assistant', content: '¡Hola! Soy Enpi, tu asistente oficial. ¿Te gustaría saber cómo nuestra IA puede ayudarte a duplicar tus ventas en Herbalife?'}]);
        }
    };

    const handleSend = async () => {
        if (!input.trim() || loading) return;

        const userMsg = input.trim();
        setInput('');
        setMessages(prev => [...prev, {role: 'user', content: userMsg}]);
        setLoading(true);

        try {
            // We use a special public endpoint for the platform agent
            // This endpoint will use the platform_distributor_id internally
            const response = await apiClient.post('/auth/platform-chat', {
                message: userMsg,
                conversation_id: conversationId,
                channel: 'webchat'
            });

            const data = response.data.data;
            setMessages(prev => [...prev, {role: 'assistant', content: data.content}]);
            if (data.conversation_id) setConversationId(data.conversation_id);
        } catch (error) {
            console.error('Chat error:', error);
            setMessages(prev => [...prev, {role: 'assistant', content: 'Lo siento, tuve un problema al procesar tu mensaje. Por favor intenta de nuevo.'}]);
        } finally {
            setLoading(false);
        }
    };

    const startRecording = async () => {
        try {
            unlockAudio();
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
            const chunks: Blob[] = [];

            recorder.ondataavailable = (e) => {
                if (e.data.size > 0) {
                    chunks.push(e.data);
                }
            };

            recorder.onstop = async () => {
                const audioBlob = new Blob(chunks, { type: 'audio/webm' });
                await sendAudioMessage(audioBlob);
                // Stop all tracks on the stream to release the microphone
                stream.getTracks().forEach(track => track.stop());
            };

            recorder.start();
            setMediaRecorder(recorder);
            setIsRecording(true);
        } catch (err) {
            console.error('Failed to start recording:', err);
            alert('No se pudo acceder al micrófono. Por favor, concede los permisos necesarios.');
        }
    };

    const stopRecording = () => {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
            setIsRecording(false);
        }
    };

    const sendAudioMessage = async (blob: Blob) => {
        setLoading(true);
        setMessages(prev => [...prev, {role: 'user', content: '🎤 Grabando nota de voz...'}]);

        try {
            const formData = new FormData();
            formData.append('file', blob, 'recording.webm');
            if (conversationId) {
                formData.append('conversation_id', conversationId.toString());
            }
            formData.append('channel', 'webchat');

            // Send voice to the interact endpoint
            const response = await apiClient.post('/voice/interact', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            });

            const data = response.data;
            
            // Replace the recording state with actual transcribed text
            setMessages(prev => {
                const copy = [...prev];
                if (copy.length > 0 && copy[copy.length - 1].role === 'user') {
                    copy[copy.length - 1].content = `🎤 ${data.user_text}`;
                }
                return copy;
            });

            // Set AI message response
            setMessages(prev => [...prev, {role: 'assistant', content: data.response_text}]);
            if (data.conversation_id) setConversationId(data.conversation_id);

            // Play the reply audio
            if (data.audio_url) {
                const apiBase = apiClient.defaults.baseURL?.replace('/api', '') || 'http://localhost:5000';
                const audio = new Audio(`${apiBase}${data.audio_url}`);
                audio.play().catch(e => console.error('Autoplay blocked or failed:', e));
            }
        } catch (error) {
            console.error('Voice interaction error:', error);
            setMessages(prev => {
                const copy = [...prev];
                if (copy.length > 0 && copy[copy.length - 1].role === 'user') {
                    copy[copy.length - 1].content = `🎤 (Error de transcripción)`;
                }
                return copy;
            });
            setMessages(prev => [...prev, {role: 'assistant', content: 'Lo siento, tuve un problema al procesar tu nota de voz. Inténtalo de nuevo.'}]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed bottom-6 right-6 z-[100] flex flex-col items-end gap-4">
            {isOpen && (
                <Card className="w-[350px] sm:w-[400px] h-[500px] shadow-2xl border-primary/20 flex flex-col animate-in slide-in-from-bottom-4 duration-300 glass">
                    <CardHeader className="p-4 border-b vivid-gradient text-white rounded-t-xl flex flex-row items-center justify-between space-y-0">
                        <div className="flex items-center gap-2">
                            <div className="h-8 w-8 rounded-full bg-white/20 flex items-center justify-center">
                                <Bot className="h-5 w-5" />
                            </div>
                            <div>
                                <CardTitle className="text-sm font-bold">Enpi AI Support</CardTitle>
                                <div className="flex items-center gap-1">
                                    <div className="h-1.5 w-1.5 rounded-full bg-green-400 animate-pulse" />
                                    <span className="text-[10px] opacity-80 uppercase font-bold">Online</span>
                                </div>
                            </div>
                        </div>
                        <Button variant="ghost" size="icon" onClick={() => setIsOpen(false)} className="text-white hover:bg-white/10 h-8 w-8">
                            <X className="h-4 w-4" />
                        </Button>
                    </CardHeader>
                    
                    <CardContent ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4 bg-background/50">
                        {messages.map((m, i) => (
                            <div key={i} className={cn(
                                "flex flex-col max-w-[85%]",
                                m.role === 'user' ? "ml-auto items-end" : "items-start"
                            )}>
                                <div className={cn(
                                    "px-3 py-2 rounded-2xl text-sm shadow-sm",
                                    m.role === 'user' 
                                        ? "bg-primary text-white rounded-tr-none" 
                                        : "bg-white/80 dark:bg-zinc-800 rounded-tl-none border border-border"
                                )}>
                                    {m.content}
                                </div>
                            </div>
                        ))}
                        {loading && (
                            <div className="flex items-center gap-2 text-muted-foreground italic text-xs animate-pulse">
                                <Loader2 className="h-3 w-3 animate-spin" />
                                Enpi está procesando...
                            </div>
                        )}
                    </CardContent>

                    <CardFooter className="p-3 border-t bg-background/80">
                        <form className="flex w-full items-center gap-2" onSubmit={(e) => { e.preventDefault(); handleSend(); }}>
                            <Button 
                                type="button"
                                size="icon" 
                                variant={isRecording ? "destructive" : "outline"}
                                className={cn(
                                    "rounded-full shrink-0 h-10 w-10 shadow-md",
                                    isRecording && "animate-pulse"
                                )}
                                onClick={isRecording ? stopRecording : startRecording}
                                disabled={loading}
                            >
                                {isRecording ? <Square className="h-4 w-4 text-white" /> : <Mic className="h-4 w-4" />}
                            </Button>
                            <Input 
                                placeholder={isRecording ? "Grabando voz..." : "Escribe tu duda..."} 
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                className="bg-white/5 border-border rounded-full"
                                disabled={isRecording || loading}
                            />
                            <Button size="icon" className="rounded-full shrink-0 vivid-gradient h-10 w-10 shadow-md" type="submit" disabled={loading || isRecording || !input.trim()}>
                                <Send className="h-4 w-4" />
                            </Button>
                        </form>
                    </CardFooter>
                </Card>
            )}

            <Button 
                onClick={handleOpen}
                className={cn(
                    "h-14 w-14 rounded-full shadow-2xl vivid-gradient hover:scale-110 transition-all duration-300 group p-0",
                    isOpen && "rotate-90"
                )}
            >
                {isOpen ? <X className="h-6 w-6" /> : <MessageCircle className="h-7 w-7 group-hover:animate-bounce" />}
            </Button>
        </div>
    );
}
