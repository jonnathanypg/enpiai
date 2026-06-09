'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useTranslation } from 'react-i18next';
import {
    LayoutDashboard,
    Users,
    Bot,
    FileText,
    HeartPulse,
    Settings,
    Radio,
    CreditCard,
    ShieldCheck,
    ChevronLeft,
    MessageSquare,
    Sparkles,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { useAuthStore } from '@/store/use-auth-store';

interface NavItem {
    titleKey: string;
    href: string;
    icon: React.ElementType;
}

// Distributor-only navigation
const distributorItems: NavItem[] = [
    { titleKey: 'sidebar.dashboard', href: '/dashboard', icon: LayoutDashboard },
    { titleKey: 'sidebar.contacts', href: '/contacts', icon: Users },
    { titleKey: 'sidebar.agentSetup', href: '/agents', icon: Bot },
    { titleKey: 'sidebar.channels', href: '/channels', icon: Radio },
    { titleKey: 'sidebar.documents', href: '/documents', icon: FileText },
    { titleKey: 'sidebar.wellness', href: '/wellness', icon: HeartPulse },
    { titleKey: 'sidebar.playground', href: '/agents/playground', icon: MessageSquare },
    { titleKey: 'sidebar.coach', href: '/coach', icon: Sparkles },
    { titleKey: 'sidebar.settings', href: '/settings', icon: Settings },
];

// Super Admin-only navigation
const adminItems: NavItem[] = [
    { titleKey: 'sidebar.dashboard', href: '/admin/dashboard', icon: ShieldCheck },
    { titleKey: 'sidebar.platformAgent', href: '/admin/platform-agent', icon: Bot },
    { titleKey: 'sidebar.systemKnowledge', href: '/admin/documents', icon: FileText },
    { titleKey: 'sidebar.billing', href: '/admin/billing', icon: CreditCard },
    { titleKey: 'sidebar.settings', href: '/settings', icon: Settings },
];

interface SidebarProps {
    collapsed: boolean;
    onToggle: () => void;
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
    const pathname = usePathname();
    const { t } = useTranslation();
    const user = useAuthStore((s) => s.user);
    const isSuperAdmin = user?.role === 'super_admin';

    // Strict isolation: each role sees ONLY its own items
    const allItems = isSuperAdmin ? adminItems : distributorItems;

    return (
        <aside
            className={cn(
                'flex h-screen flex-col border-r bg-sidebar/60 backdrop-blur-xl transition-all duration-300 glass',
                collapsed ? 'w-16' : 'w-64'
            )}
        >
            {/* Logo */}
            <div className={cn(
                "flex h-16 items-center border-b border-white/10 px-4",
                collapsed ? "justify-center" : "justify-start gap-3"
            )}>
                <div className="flex items-center justify-center w-8 h-8 shrink-0">
                    <img src="/favicon-enpiai-ligth.png" alt="Enpi AI" className="w-full h-full object-contain dark:hidden" />
                    <img src="/favicon-enpiai-dark.png" alt="Enpi AI" className="w-full h-full object-contain hidden dark:block" />
                </div>
                {!collapsed && (
                    <span className="text-xl font-bold tracking-tight">
                        Enpi<span className="bg-gradient-to-r from-green-500 to-emerald-500 bg-clip-text text-transparent">AI</span>
                    </span>
                )}
                {!collapsed && (
                    <div className="flex-1" />
                )}
                {!collapsed && (
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={onToggle}
                        className="h-8 w-8 hover:bg-white/10"
                    >
                        <ChevronLeft
                            className={cn(
                                'h-4 w-4 transition-transform text-muted-foreground',
                                collapsed && 'rotate-180'
                            )}
                        />
                    </Button>
                )}
                {collapsed && (
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={onToggle}
                        className="absolute -right-3 top-20 h-6 w-6 rounded-full bg-background border shadow-sm z-50"
                    >
                        <ChevronLeft className="h-3 w-3 rotate-180" />
                    </Button>
                )}
            </div>

            {/* Navigation */}
            <nav className="flex-1 space-y-1.5 overflow-y-auto p-3">
                {allItems.map((item) => {
                    const isActive =
                        pathname === item.href || pathname.startsWith(item.href + '/');
                    return (
                        <Link key={item.href} href={item.href}>
                            <span
                                className={cn(
                                    'flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold transition-all duration-200 group',
                                    isActive
                                        ? 'bg-gradient-to-r from-primary/20 to-secondary/10 text-primary border border-primary/20 shadow-sm'
                                        : 'text-sidebar-foreground/60 hover:bg-white/5 hover:text-sidebar-foreground',
                                    collapsed && 'justify-center px-2'
                                )}
                            >
                                <item.icon className={cn(
                                    "h-5 w-5 shrink-0 transition-transform group-hover:scale-110",
                                    isActive ? "text-primary" : "text-sidebar-foreground/40"
                                )} />
                                {!collapsed && t(item.titleKey)}
                            </span>
                        </Link>
                    );
                })}
            </nav>
        </aside>
    );
}
