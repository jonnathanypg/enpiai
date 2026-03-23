import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import en from '@/locales/en/translation.json';
import es from '@/locales/es/translation.json';
import pt from '@/locales/pt/translation.json';

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    es: { translation: es },
    pt: { translation: pt },
  },
  lng: typeof window !== 'undefined' ? (localStorage.getItem('i18nextLng') || 'en') : 'en',
  fallbackLng: 'en',
  interpolation: {
    escapeValue: false, // React already escapes
  },
});

export default i18n;
