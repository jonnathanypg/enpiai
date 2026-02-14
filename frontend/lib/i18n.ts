'use client';

import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import resourcesToBackend from 'i18next-resources-to-backend';

i18n
    .use(initReactI18next)
    .use(
        resourcesToBackend((language: string, namespace: string) =>
            import(`@/locales/${language}/${namespace}.json`)
        )
    )
    .init({
        lng: 'en', // Default, will be overwritten by AuthStore
        fallbackLng: 'en',
        ns: ['common'],
        defaultNS: 'common',
        interpolation: {
            escapeValue: false, // React escapes by default
        },
        react: {
            useSuspense: true,
        },
    });

export default i18n;
