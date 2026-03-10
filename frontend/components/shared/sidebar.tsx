'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
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
    title: string;
    href: string;
    icon: React.ElementType;
    adminOnly?: boolean;
}

// Distributor-only navigation
const distributorItems: NavItem[] = [
    { title: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { title: 'Contacts', href: '/contacts', icon: Users },
    { title: 'Agent Setup', href: '/agents', icon: Bot },
    { title: 'Channels', href: '/channels', icon: Radio },
    { title: 'Documents', href: '/documents', icon: FileText },
    { title: 'Wellness', href: '/wellness', icon: HeartPulse },
    { title: 'Playground', href: '/agents/playground', icon: MessageSquare },
    { title: 'Settings', href: '/settings', icon: Settings },
];

// Super Admin-only navigation
const adminItems: NavItem[] = [
    { title: 'Dashboard', href: '/admin/dashboard', icon: ShieldCheck },
    { title: 'System Knowledge', href: '/admin/documents', icon: FileText },
];

interface SidebarProps {
    collapsed: boolean;
    onToggle: () => void;
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
    const pathname = usePathname();
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
                                {!collapsed && item.title}
                            </span>
                        </Link>
                    );
                })}
            </nav>
        </aside>
    );
}
