import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import Cookies from 'js-cookie';
import type { User } from '@/types';

interface AuthState {
    user: User | null;
    isAuthenticated: boolean;
    language: string;
    login: (user: User, accessToken: string, refreshToken: string) => void;
    logout: () => void;
    setLanguage: (lang: string) => void;
    hydrated: boolean;
}

export const useAuthStore = create<AuthState>()(
    persist(
        (set) => ({
            user: null,
            isAuthenticated: false,
            language: 'en',
            hydrated: false,
            login: (user, accessToken, refreshToken) => {
                Cookies.set('access_token', accessToken, { expires: 1 }); // 1 day
                Cookies.set('refresh_token', refreshToken, { expires: 7 });
                set({ user, isAuthenticated: true, language: 'en' }); // Default en, should come from backend
            },
            logout: () => {
                Cookies.remove('access_token');
                Cookies.remove('refresh_token');
                set({ user: null, isAuthenticated: false });
            },
            setLanguage: (lang) => set({ language: lang }),
        }),
        {
            name: 'auth-storage',
            onRehydrateStorage: () => (state) => {
                if (state) state.hydrated = true;
            },
        }
    )
);
