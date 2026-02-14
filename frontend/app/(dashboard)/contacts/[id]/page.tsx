'use client';

import { useQuery } from '@tanstack/react-query';
import {
    User,
    Phone,
    Mail,
    MapPin,
    Calendar,
    MoreVertical,
    MessageSquare,
    FileText,
    Activity,
    ArrowLeft,
} from 'lucide-react';
import Link from 'next/link';
import { format } from 'date-fns';

import { Button } from '@/components/ui/button';
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { LeadTimeline } from '@/components/features/lead-timeline';
import apiClient from '@/lib/api-client';
import type { UnifiedContact } from '@/types';

export default function UnifiedContactPage({ params }: { params: { id: string } }) {
    const { id } = params;

    const { data: contact, isLoading } = useQuery({
        queryKey: ['unified-contact', id],
        queryFn: async () => {
            const { data } = await apiClient.get<{ data: UnifiedContact }>(`/contacts/unified/${id}`);
            return data.data;
        },
    });

    if (isLoading) {
        return <div className="space-y-4"><Skeleton className="h-48 w-full" /><Skeleton className="h-96 w-full" /></div>;
    }

    if (!contact) {
        return <div>Contact not found</div>;
    }

    const profile = contact.lead || contact.customer;
    if (!profile) return <div>Invalid contact data</div>;

    const initials = `${profile.first_name?.[0] || ''}${profile.last_name?.[0] || ''}`;
    const statusColor = profile.status === 'qualified' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700';

    return (
        <div className="space-y-6">
            {/* Header / Breadcrumb */}
            <div className="flex items-center gap-2">
                <Link href="/contacts">
                    <Button variant="ghost" size="icon">
                        <ArrowLeft className="h-4 w-4" />
                    </Button>
                </Link>
                <h1 className="text-xl font-semibold">Contact Profile</h1>
            </div>

            <div className="grid gap-6 lg:grid-cols-12">
                {/* Left Column: Profile Card */}
                <div className="lg:col-span-4 space-y-6">
                    <Card>
                        <CardContent className="pt-6">
                            <div className="flex flex-col items-center text-center">
                                <Avatar className="h-24 w-24">
                                    <AvatarImage src="" />
                                    <AvatarFallback className="text-2xl">{initials}</AvatarFallback>
                                </Avatar>
                                <h2 className="mt-4 text-xl font-bold">
                                    {profile.first_name} {profile.last_name}
                                </h2>
                                <Badge variant="secondary" className="mt-2 capitalize">
                                    {/* Handle specific status logic from UnifiedContact resolver */}
                                    {profile.status}
                                </Badge>

                                <div className="mt-6 w-full space-y-4 text-left">
                                    <div className="flex items-center gap-3 text-sm">
                                        <Mail className="h-4 w-4 text-muted-foreground" />
                                        <span>{profile.email || 'No email'}</span>
                                    </div>
                                    <div className="flex items-center gap-3 text-sm">
                                        <Phone className="h-4 w-4 text-muted-foreground" />
                                        <span>{profile.phone || 'No phone'}</span>
                                    </div>
                                    <div className="flex items-center gap-3 text-sm">
                                        <Calendar className="h-4 w-4 text-muted-foreground" />
                                        <span>Added {format(new Date(profile.created_at), 'PPP')}</span>
                                    </div>
                                </div>

                                <div className="mt-8 flex w-full gap-2">
                                    <Button className="flex-1">
                                        <MessageSquare className="mr-2 h-4 w-4" /> Message
                                    </Button>
                                    <Button variant="outline" size="icon">
                                        <MoreVertical className="h-4 w-4" />
                                    </Button>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Wellness Summary (If available) */}
                    {contact.evaluations.length > 0 && (
                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2 text-base">
                                    <Activity className="h-4 w-4" /> Wellness Stats
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-2 text-sm">
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">Latest BMI:</span>
                                    <span className="font-bold">{contact.evaluations[0].bmi?.toFixed(1)}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">Goal:</span>
                                    <span>{contact.evaluations[0].primary_goal}</span>
                                </div>
                                <Button variant="link" className="px-0 text-primary">View Full Report</Button>
                            </CardContent>
                        </Card>
                    )}
                </div>

                {/* Right Column: Timeline & Tabs */}
                <div className="lg:col-span-8">
                    <Tabs defaultValue="timeline" className="w-full">
                        <TabsList className="grid w-full grid-cols-3">
                            <TabsTrigger value="timeline">Timeline 360°</TabsTrigger>
                            <TabsTrigger value="wellness">Wellness</TabsTrigger>
                            <TabsTrigger value="notes">Notes & Tasks</TabsTrigger>
                        </TabsList>

                        <TabsContent value="timeline" className="mt-6">
                            <Card>
                                <CardHeader>
                                    <CardTitle>Interaction History</CardTitle>
                                    <CardDescription>
                                        All messages, appointments, and system events.
                                    </CardDescription>
                                </CardHeader>
                                <CardContent>
                                    <LeadTimeline
                                        conversations={contact.conversations}
                                        appointments={contact.appointments}
                                        evaluations={contact.evaluations}
                                    />
                                </CardContent>
                            </Card>
                        </TabsContent>

                        <TabsContent value="wellness" className="mt-6">
                            <div className="flex h-64 items-center justify-center rounded-lg border border-dashed text-muted-foreground">
                                <p>Wellness charts coming soon.</p>
                            </div>
                        </TabsContent>
                        <TabsContent value="notes" className="mt-6">
                            <div className="flex h-64 items-center justify-center rounded-lg border border-dashed text-muted-foreground">
                                <p>Notes functionality coming soon.</p>
                            </div>
                        </TabsContent>
                    </Tabs>
                </div>
            </div>
        </div>
    );
}
