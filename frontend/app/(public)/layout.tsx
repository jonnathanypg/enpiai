'use client';

import Link from 'next/link';
import { useTranslation } from 'react-i18next';

export default function PublicLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const { t } = useTranslation();

    return (
        <div className="flex min-h-screen flex-col bg-muted/30 text-foreground transition-colors duration-300">
            {/* MAIN CONTENT */}
            <main className="flex-1">
                {children}
            </main>

            {/* PUBLIC FOOTER */}
            <footer className="border-t py-8 bg-card">
                <div className="mx-auto max-w-6xl px-4 sm:px-6">
                    <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <span>Powered by</span>
                            <img src="/favicon-enpiai-ligth.png" alt="Enpi AI" className="h-5 w-auto object-contain dark:hidden" />
                            <img src="/favicon-enpiai-dark.png" alt="Enpi AI" className="h-5 w-auto object-contain hidden dark:block" />
                        </div>
                        <div className="flex flex-wrap items-center justify-center gap-6">
                            <Link href="/privacy" id="privacy-policy-link" className="text-xs text-muted-foreground hover:text-green-500 transition-colors">
                                {t('legal.privacyTitle', 'Política de Privacidad')}
                            </Link>
                            <Link href="/terms" className="text-xs text-muted-foreground hover:text-green-500 transition-colors">
                                {t('legal.termsTitle', 'Condiciones del Servicio')}
                            </Link>
                            <Link href="/refunds" className="text-xs text-muted-foreground hover:text-green-500 transition-colors">
                                {t('legal.refundsTitle', 'Política de Reembolso')}
                            </Link>
                            <p className="text-xs text-muted-foreground">
                                © {new Date().getFullYear()} WEBLIFETECH. {t('home.footer.legal')}
                            </p>
                        </div>
                    </div>
                </div>
            </footer>
        </div>
    );
}
