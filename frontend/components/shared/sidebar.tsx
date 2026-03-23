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
    { titleKey: 'sidebar.settings', href: '/settings', icon: Settings },
];

// Super Admin-only navigation
const adminItems: NavItem[] = [
    { titleKey: 'sidebar.dashboard', href: '/admin/dashboard', icon: ShieldCheck },
    { titleKey: 'sidebar.systemKnowledge', href: '/admin/documents', icon: FileText },
    { titleKey: 'sidebar.billing', href: '/admin/billing', icon: CreditCard },
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
                'flex h-screen flex-col border-r bg-sidebar transition-all duration-300',
                collapsed ? 'w-16' : 'w-64'
            )}
        >
            {/* Logo */}
            <div className="flex h-16 items-center justify-between border-b px-4">
                {!collapsed && (
                    <span className="text-lg font-bold tracking-tight">
                        Enpi<span className="text-primary">AI</span>
                    </span>
                )}
                <Button
                    variant="ghost"
                    size="icon"
                    onClick={onToggle}
                    className="h-8 w-8"
                >
                    <ChevronLeft
                        className={cn(
                            'h-4 w-4 transition-transform',
                            collapsed && 'rotate-180'
                        )}
                    />
                </Button>
            </div>

            {/* Navigation */}
            <nav className="flex-1 space-y-1 overflow-y-auto p-2">
                {allItems.map((item) => {
                    const isActive =
                        pathname === item.href || pathname.startsWith(item.href + '/');
                    return (
                        <Link key={item.href} href={item.href}>
                            <span
                                className={cn(
                                    'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                                    isActive
                                        ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                                        : 'text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground',
                                    collapsed && 'justify-center px-2'
                                )}
                            >
                                <item.icon className="h-5 w-5 shrink-0" />
                                {!collapsed && t(item.titleKey)}
                            </span>
                        </Link>
                    );
                })}
            </nav>
        </aside>
    );
}
