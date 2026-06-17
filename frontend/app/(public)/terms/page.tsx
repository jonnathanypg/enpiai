'use client';

import { useTranslation } from 'react-i18next';
import { Leaf, ArrowLeft, ArrowRight } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { LanguageSwitcher } from '@/components/shared/language-switcher';
import { ThemeToggle } from '@/components/shared/theme-toggle';

export default function TermsPage() {
    const { t } = useTranslation();
    const currentDate = new Date().toLocaleDateString();

    return (
        <div className="flex min-h-screen flex-col bg-background text-foreground transition-colors duration-300">
            {/* Header Navigation */}
            <header className="sticky top-0 z-50 border-b border-border bg-background">
                <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
                    <Link href="/" className="flex items-center">
                        <img src="/favicon-enpiai-ligth.png" alt="Enpi AI" className="h-8 w-auto object-contain dark:hidden" />
                        <img src="/favicon-enpiai-dark.png" alt="Enpi AI" className="h-8 w-auto object-contain hidden dark:block" />
                    </Link>

                    <nav className="hidden items-center gap-6 text-sm text-muted-foreground md:flex">
                        <Link href="/#features" className="transition-colors hover:text-foreground">
                            {t('home.nav.features')}
                        </Link>
                        <Link href="/#how-it-works" className="transition-colors hover:text-foreground">
                            {t('home.nav.howItWorks')}
                        </Link>
                        <Link href="/pricing" className="transition-colors hover:text-foreground">
                            {t('home.nav.pricing')}
                        </Link>
                    </nav>

                    <div className="flex items-center gap-3">
                        <LanguageSwitcher />
                        <ThemeToggle />
                        <Link href="/login" className="hidden sm:block">
                            <Button variant="ghost" size="sm">
                                {t('home.hero.signIn')}
                            </Button>
                        </Link>
                        <Link href="/register">
                            <Button size="sm" className="bg-gradient-to-r from-green-500 to-emerald-600 text-white shadow-md shadow-green-500/25 hover:shadow-lg hover:shadow-green-500/30 transition-all border-0">
                                {t('auth.register')} <ArrowRight className="ml-1 h-4 w-4" />
                            </Button>
                        </Link>
                    </div>
                </div>
            </header>

            {/* Main content */}
            <main className="flex-1 mx-auto w-full max-w-4xl px-4 py-12 relative">
                {/* Decorative background gradients */}
                <div className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
                    <div className="absolute top-20 right-10 h-72 w-72 rounded-full bg-green-500/5 blur-3xl" />
                    <div className="absolute bottom-20 left-10 h-72 w-72 rounded-full bg-emerald-500/5 blur-3xl" />
                </div>

                <div className="mb-8">
                    <Link href="/">
                        <Button variant="ghost" size="sm" className="gap-2 hover:bg-muted/80">
                            <ArrowLeft className="w-4 h-4" />
                            {t('common.back', { defaultValue: 'Volver' })}
                        </Button>
                    </Link>
                </div>

                <div className="bg-card/70 border backdrop-blur-md rounded-2xl p-8 md:p-12 shadow-xl relative overflow-hidden">
                    {/* Leaf icon background pattern */}
                    <div className="absolute top-0 right-0 p-12 opacity-[0.03] pointer-events-none">
                        <Leaf className="w-64 h-64 text-green-500" />
                    </div>

                    <header className="mb-12 border-b pb-8">
                        <h1 className="text-4xl font-extrabold tracking-tight mb-4 flex items-center gap-3 bg-gradient-to-r from-green-600 to-emerald-500 bg-clip-text text-transparent">
                            <Leaf className="text-green-500 w-10 h-10 shrink-0" />
                            {t('legal.termsTitle')}
                        </h1>
                        <p className="text-muted-foreground text-sm font-medium">
                            {t('legal.lastUpdated', { date: currentDate })}
                        </p>
                    </header>

                    <div className="prose prose-slate dark:prose-invert max-w-none space-y-8 text-sm md:text-base leading-relaxed">
                        <section>
                            <p className="text-lg text-muted-foreground leading-relaxed">
                                {t('legal.terms.intro')}
                            </p>
                        </section>

                        <section className="space-y-3">
                            <h2 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
                                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-green-100 dark:bg-green-950 text-green-600 text-sm font-semibold">1</span>
                                {t('legal.terms.sections.acceptance.title')}
                            </h2>
                            <p className="text-muted-foreground">
                                {t('legal.terms.sections.acceptance.content')}
                            </p>
                        </section>

                        <section className="space-y-3">
                            <h2 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
                                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-green-100 dark:bg-green-950 text-green-600 text-sm font-semibold">2</span>
                                {t('legal.terms.sections.service.title')}
                            </h2>
                            <p className="text-muted-foreground">
                                {t('legal.terms.sections.service.content')}
                            </p>
                        </section>

                        <section className="space-y-3">
                            <h2 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
                                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-green-100 dark:bg-green-950 text-green-600 text-sm font-semibold">3</span>
                                {t('legal.terms.sections.responsibility.title')}
                            </h2>
                            <p className="text-muted-foreground">
                                {t('legal.terms.sections.responsibility.content')}
                            </p>
                            <ul className="grid gap-2 pl-4 mt-2">
                                <li className="flex items-start gap-2 text-muted-foreground">
                                    <span className="h-1.5 w-1.5 rounded-full bg-green-500 mt-2 shrink-0" />
                                    <span>{t('legal.terms.sections.responsibility.item1')}</span>
                                </li>
                                <li className="flex items-start gap-2 text-muted-foreground">
                                    <span className="h-1.5 w-1.5 rounded-full bg-green-500 mt-2 shrink-0" />
                                    <span>{t('legal.terms.sections.responsibility.item2')}</span>
                                </li>
                                <li className="flex items-start gap-2 text-muted-foreground">
                                    <span className="h-1.5 w-1.5 rounded-full bg-green-500 mt-2 shrink-0" />
                                    <span>{t('legal.terms.sections.responsibility.item3')}</span>
                                </li>
                            </ul>
                        </section>

                        <section className="space-y-3">
                            <h2 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
                                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-green-100 dark:bg-green-950 text-green-600 text-sm font-semibold">4</span>
                                {t('legal.terms.sections.payments.title')}
                            </h2>
                            <p className="text-muted-foreground">
                                {t('legal.terms.sections.payments.content')}
                            </p>
                        </section>

                        <section className="space-y-3">
                            <h2 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
                                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-green-100 dark:bg-green-950 text-green-600 text-sm font-semibold">5</span>
                                {t('legal.terms.sections.liability.title')}
                            </h2>
                            <p className="text-muted-foreground">
                                {t('legal.terms.sections.liability.content')}
                            </p>
                        </section>

                        <footer className="pt-8 border-t text-sm text-muted-foreground mt-12">
                            {t('legal.privacy.sections.contact.content')}
                        </footer>
                    </div>
                </div>
            </main>
        </div>
    );
}
