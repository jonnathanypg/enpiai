'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useTheme } from 'next-themes';
import { useTranslation } from 'react-i18next';
import { Moon, Sun, LogOut, Menu, User as UserIcon, Shield } from 'lucide-react';
import Cookies from 'js-cookie';

import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
    DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import { useAuthStore } from '@/store/use-auth-store';
import { LanguageSwitcher } from './language-switcher';

interface HeaderProps {
    onMobileMenuToggle: () => void;
}

export function Header({ onMobileMenuToggle }: HeaderProps) {
    const router = useRouter();
    const { t } = useTranslation();
    const { theme, setTheme } = useTheme();
    const user = useAuthStore((s) => s.user);
    const logout = useAuthStore((s) => s.logout);

    const handleLogout = () => {
        logout();
        router.push('/login');
    };

    const initials = user?.name
        ? user.name
            .split(' ')
            .map((n) => n[0])
            .join('')
            .toUpperCase()
            .slice(0, 2)
        : 'U';

    const [isOverride, setIsOverride] = useState(false);

    useEffect(() => {
        setIsOverride(!!Cookies.get('distributor_id_override'));
    }, []);

    const clearOverride = () => {
        Cookies.remove('distributor_id_override');
        setIsOverride(false);
        window.location.reload();
    };

    return (
        <header className="sticky top-0 z-40 flex h-16 items-center justify-between border-b bg-background/60 px-4 backdrop-blur-md glass">
            {/* Mobile menu button */}
            <Button
                variant="ghost"
                size="icon"
                className="lg:hidden hover:bg-white/10"
                onClick={onMobileMenuToggle}
            >
                <Menu className="h-5 w-5" />
            </Button>

            {/* Logo for mobile */}
            <div className="flex lg:hidden ml-2">
                 <span className="text-lg font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                    Enpi AI
                </span>
            </div>

            {/* Override Indicator */}
            {isOverride && (
                <div className="ml-4 flex items-center gap-2 px-3 py-1 rounded-full bg-secondary/20 border border-secondary/30 animate-pulse">
                    <Shield className="h-3 w-3 text-secondary" />
                    <span className="text-[10px] font-bold text-secondary uppercase tracking-tight">Contexto Externo</span>
                    <Button variant="ghost" size="icon" className="h-5 w-5 hover:bg-secondary/20" onClick={clearOverride}>
                        <LogOut className="h-3 w-3" />
                    </Button>
                </div>
            )}

            {/* Spacer */}
            <div className="flex-1" />

            {/* Right side actions */}
            <div className="flex items-center gap-3">
                {/* Language Switcher */}
                <div className="hidden sm:block">
                    <LanguageSwitcher />
                </div>

                {/* Theme toggle */}
                <Button
                    variant="ghost"
                    size="icon"
                    className="hover:bg-white/10"
                    onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                >
                    <Sun className="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0 text-primary" />
                    <Moon className="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100 text-secondary" />
                </Button>

                {/* User menu */}
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button variant="ghost" className="flex items-center gap-2 px-2 hover:bg-white/10 group">
                            <Avatar className="h-8 w-8 ring-2 ring-primary/20 transition-all group-hover:ring-primary/50">
                                <AvatarFallback className="bg-gradient-to-br from-primary/20 to-secondary/20 text-xs font-bold">{initials}</AvatarFallback>
                            </Avatar>
                            <span className="hidden text-sm font-semibold md:inline-block">
                                {user?.name}
                            </span>
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-56 glass-card p-2">
                        <div className="px-2 py-1.5 mb-1">
                            <p className="text-xs text-muted-foreground uppercase font-bold tracking-wider">{t('common.userAccount') || 'Cuenta'}</p>
                        </div>
                        <DropdownMenuItem onClick={() => router.push('/settings')} className="rounded-lg cursor-pointer">
                            <UserIcon className="mr-2 h-4 w-4 text-primary" />
                            {t('common.profile')}
                        </DropdownMenuItem>
                        <DropdownMenuSeparator className="bg-white/10" />
                        <DropdownMenuItem onClick={handleLogout} className="rounded-lg cursor-pointer text-destructive focus:text-destructive">
                            <LogOut className="mr-2 h-4 w-4" />
                            {t('common.logOut')}
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
            </div>
        </header>
    );
}
