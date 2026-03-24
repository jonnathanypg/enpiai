'use client';

import Link from 'next/link';
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';
import { LanguageSwitcher } from '@/components/shared/language-switcher';
import {
  ArrowRight,
  Bot,
  Shield,
  Zap,
  MessageCircle,
  Calendar,
  BarChart3,
  FileText,
  CheckCircle2,
  Sparkles,
  Globe,
  Users,
  HeartPulse,
  Leaf,
} from 'lucide-react';

export default function HomePage() {
  const { t } = useTranslation();

  return (
    <div className="flex min-h-screen flex-col bg-background">
      {/* ═══════════════════════════════════════════════
          NAVIGATION
      ═══════════════════════════════════════════════ */}
      <header className="sticky top-0 z-50 border-b border-border/40 bg-background/80 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-green-500 to-emerald-600 text-white text-sm font-bold shadow-md shadow-green-500/20">
              E
            </div>
            <span className="text-xl font-bold tracking-tight">
              Enpi<span className="bg-gradient-to-r from-green-500 to-emerald-500 bg-clip-text text-transparent">AI</span>
            </span>
          </div>

          <nav className="hidden items-center gap-6 text-sm text-muted-foreground md:flex">
            <a href="#features" className="transition-colors hover:text-foreground">
              {t('home.nav.features')}
            </a>
            <a href="#how-it-works" className="transition-colors hover:text-foreground">
              {t('home.nav.howItWorks')}
            </a>
            <a href="#pricing" className="transition-colors hover:text-foreground">
              {t('home.nav.pricing')}
            </a>
          </nav>

          <div className="flex items-center gap-3">
            <LanguageSwitcher />
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

      {/* ═══════════════════════════════════════════════
          HERO SECTION
      ═══════════════════════════════════════════════ */}
      <section className="relative overflow-hidden">
        {/* Background decoration */}
        <div className="pointer-events-none absolute inset-0 -z-10">
          <div className="absolute -top-40 right-0 h-[500px] w-[500px] rounded-full bg-green-500/5 blur-3xl" />
          <div className="absolute -bottom-20 -left-20 h-[400px] w-[400px] rounded-full bg-emerald-500/5 blur-3xl" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[600px] w-[600px] rounded-full bg-green-400/3 blur-3xl" />
        </div>

        <div className="mx-auto max-w-6xl px-4 py-24 sm:px-6 sm:py-32 lg:py-40">
          <div className="mx-auto max-w-3xl text-center">
            {/* Badge */}
            <div className="inline-flex items-center rounded-full border border-green-500/20 bg-green-500/5 px-4 py-1.5 text-sm text-green-600 dark:text-green-400 mb-8">
              <Leaf className="mr-2 h-3.5 w-3.5" />
              {t('home.hero.badge')}
            </div>

            <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl lg:text-6xl leading-[1.1]">
              {t('home.hero.title')}
              <br />
              <span className="bg-gradient-to-r from-green-500 via-emerald-500 to-teal-500 bg-clip-text text-transparent">
                {t('home.hero.titleAccent')}
              </span>
            </h1>

            <p className="mx-auto mt-6 max-w-xl text-lg text-muted-foreground leading-relaxed">
              {t('home.hero.description')}
            </p>

            <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
              <Link href="/register">
                <Button size="lg" className="px-8 bg-gradient-to-r from-green-500 to-emerald-600 text-white shadow-lg shadow-green-500/25 hover:shadow-xl hover:shadow-green-500/30 hover:scale-[1.02] transition-all border-0 text-base">
                  <Sparkles className="mr-2 h-4 w-4" />
                  {t('home.hero.cta')}
                </Button>
              </Link>
              <Link href="/login">
                <Button variant="outline" size="lg" className="px-8 text-base">
                  {t('home.hero.signIn')}
                </Button>
              </Link>
            </div>

            {/* Trust badges */}
            <div className="mt-12 flex flex-wrap items-center justify-center gap-x-8 gap-y-3 text-sm text-muted-foreground">
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4 text-green-500" /> {t('home.hero.trustNoCard')}
              </div>
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4 text-green-500" /> {t('home.hero.trustSetup')}
              </div>
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="h-4 w-4 text-green-500" /> {t('home.hero.trustChannels')}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════
          FEATURES GRID
      ═══════════════════════════════════════════════ */}
      <section id="features" className="border-t bg-muted/30 py-24">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="text-center mb-16">
            <div className="inline-flex items-center rounded-full border border-green-500/20 bg-green-500/5 px-3 py-1 text-xs font-medium text-green-600 dark:text-green-400 mb-4">
              {t('home.features.badge')}
            </div>
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
              {t('home.features.title')}{' '}
              <span className="bg-gradient-to-r from-green-500 to-emerald-500 bg-clip-text text-transparent">
                {t('home.features.titleAccent')}
              </span>
            </h2>
            <p className="mx-auto mt-4 max-w-lg text-muted-foreground">
              {t('home.features.description')}
            </p>
          </div>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {/* Feature 1 */}
            <div className="group relative rounded-2xl border bg-card p-6 shadow-sm transition-all hover:shadow-md hover:border-green-500/30">
              <div className="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-green-500/10 to-emerald-500/10 text-green-600 dark:text-green-400">
                <Bot className="h-5 w-5" />
              </div>
              <h3 className="font-semibold text-base">{t('home.features.items.agents.title')}</h3>
              <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                {t('home.features.items.agents.description')}
              </p>
            </div>

            {/* Feature 2 */}
            <div className="group relative rounded-2xl border bg-card p-6 shadow-sm transition-all hover:shadow-md hover:border-green-500/30">
              <div className="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-green-500/10 to-emerald-500/10 text-green-600 dark:text-green-400">
                <MessageCircle className="h-5 w-5" />
              </div>
              <h3 className="font-semibold text-base">{t('home.features.items.channels.title')}</h3>
              <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                {t('home.features.items.channels.description')}
              </p>
            </div>

            {/* Feature 3 */}
            <div className="group relative rounded-2xl border bg-card p-6 shadow-sm transition-all hover:shadow-md hover:border-green-500/30">
              <div className="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-green-500/10 to-emerald-500/10 text-green-600 dark:text-green-400">
                <HeartPulse className="h-5 w-5" />
              </div>
              <h3 className="font-semibold text-base">{t('home.features.items.wellness.title')}</h3>
              <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                {t('home.features.items.wellness.description')}
              </p>
            </div>

            {/* Feature 4 */}
            <div className="group relative rounded-2xl border bg-card p-6 shadow-sm transition-all hover:shadow-md hover:border-green-500/30">
              <div className="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-green-500/10 to-emerald-500/10 text-green-600 dark:text-green-400">
                <Users className="h-5 w-5" />
              </div>
              <h3 className="font-semibold text-base">{t('home.features.items.crm.title')}</h3>
              <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                {t('home.features.items.crm.description')}
              </p>
            </div>

            {/* Feature 5 */}
            <div className="group relative rounded-2xl border bg-card p-6 shadow-sm transition-all hover:shadow-md hover:border-green-500/30">
              <div className="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-green-500/10 to-emerald-500/10 text-green-600 dark:text-green-400">
                <Calendar className="h-5 w-5" />
              </div>
              <h3 className="font-semibold text-base">{t('home.features.items.scheduling.title')}</h3>
              <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                {t('home.features.items.scheduling.description')}
              </p>
            </div>

            {/* Feature 6 */}
            <div className="group relative rounded-2xl border bg-card p-6 shadow-sm transition-all hover:shadow-md hover:border-green-500/30">
              <div className="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-green-500/10 to-emerald-500/10 text-green-600 dark:text-green-400">
                <FileText className="h-5 w-5" />
              </div>
              <h3 className="font-semibold text-base">{t('home.features.items.knowledge.title')}</h3>
              <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
                {t('home.features.items.knowledge.description')}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════
          HOW IT WORKS
      ═══════════════════════════════════════════════ */}
      <section id="how-it-works" className="py-24">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="text-center mb-16">
            <div className="inline-flex items-center rounded-full border border-green-500/20 bg-green-500/5 px-3 py-1 text-xs font-medium text-green-600 dark:text-green-400 mb-4">
              {t('home.howItWorks.badge')}
            </div>
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
              {t('home.howItWorks.title')}{' '}
              <span className="bg-gradient-to-r from-green-500 to-emerald-500 bg-clip-text text-transparent">
                {t('home.howItWorks.titleAccent')}
              </span>
            </h2>
          </div>

          <div className="grid gap-8 sm:grid-cols-3">
            {/* Step 1 */}
            <div className="relative text-center">
              <div className="mx-auto mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-green-500 to-emerald-600 text-white font-bold text-lg shadow-lg shadow-green-500/20">
                1
              </div>
              <h3 className="font-semibold text-lg mb-2">{t('home.howItWorks.steps.step1.title')}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {t('home.howItWorks.steps.step1.description')}
              </p>
            </div>

            {/* Step 2 */}
            <div className="relative text-center">
              <div className="mx-auto mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-green-500 to-emerald-600 text-white font-bold text-lg shadow-lg shadow-green-500/20">
                2
              </div>
              <h3 className="font-semibold text-lg mb-2">{t('home.howItWorks.steps.step2.title')}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {t('home.howItWorks.steps.step2.description')}
              </p>
            </div>

            {/* Step 3 */}
            <div className="relative text-center">
              <div className="mx-auto mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-green-500 to-emerald-600 text-white font-bold text-lg shadow-lg shadow-green-500/20">
                3
              </div>
              <h3 className="font-semibold text-lg mb-2">{t('home.howItWorks.steps.step3.title')}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {t('home.howItWorks.steps.step3.description')}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════
          STATS SECTION
      ═══════════════════════════════════════════════ */}
      <section className="border-y bg-gradient-to-r from-green-500 to-emerald-600 py-16">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="grid gap-8 text-center text-white sm:grid-cols-4">
            <div>
              <div className="text-4xl font-extrabold">24/7</div>
              <div className="mt-1 text-sm text-white/70">{t('home.stats.alwaysAvailable')}</div>
            </div>
            <div>
              <div className="text-4xl font-extrabold">+40%</div>
              <div className="mt-1 text-sm text-white/70">{t('home.stats.channels')}</div>
            </div>
            <div>
              <div className="text-4xl font-extrabold">20h+</div>
              <div className="mt-1 text-sm text-white/70">{t('home.stats.setupTime')}</div>
            </div>
            <div>
              <div className="text-4xl font-extrabold">100%</div>
              <div className="mt-1 text-sm text-white/70">{t('home.stats.conversations')}</div>
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════
          SECURITY & DATA
      ═══════════════════════════════════════════════ */}
      <section className="py-24">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="grid items-center gap-12 lg:grid-cols-2">
            <div>
              <div className="inline-flex items-center rounded-full border border-green-500/20 bg-green-500/5 px-3 py-1 text-xs font-medium text-green-600 dark:text-green-400 mb-4">
                {t('home.security.badge')}
              </div>
              <h2 className="text-3xl font-bold tracking-tight sm:text-4xl mb-4">
                {t('home.security.title')}{' '}
                <span className="bg-gradient-to-r from-green-500 to-emerald-500 bg-clip-text text-transparent">
                  {t('home.security.titleAccent')}
                </span>
              </h2>
              <p className="text-muted-foreground leading-relaxed mb-8">
                {t('home.security.description')}
              </p>

              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-green-500/10 text-green-600 dark:text-green-400">
                    <Shield className="h-3.5 w-3.5" />
                  </div>
                  <div>
                    <div className="font-medium text-sm">{t('home.security.encryption.title')}</div>
                    <div className="text-sm text-muted-foreground">{t('home.security.encryption.description')}</div>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-green-500/10 text-green-600 dark:text-green-400">
                    <Globe className="h-3.5 w-3.5" />
                  </div>
                  <div>
                    <div className="font-medium text-sm">{t('home.security.isolation.title')}</div>
                    <div className="text-sm text-muted-foreground">{t('home.security.isolation.description')}</div>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-green-500/10 text-green-600 dark:text-green-400">
                    <Zap className="h-3.5 w-3.5" />
                  </div>
                  <div>
                    <div className="font-medium text-sm">{t('home.security.i18n.title')}</div>
                    <div className="text-sm text-muted-foreground">{t('home.security.i18n.description')}</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Visual card */}
            <div className="relative">
              <div className="rounded-2xl border bg-card p-8 shadow-xl shadow-green-500/5">
                <div className="space-y-4">
                  <div className="flex items-center gap-3 rounded-xl bg-muted/50 p-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-500/10 text-green-600 dark:text-green-400">
                      <Bot className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="text-sm font-medium">{t('home.security.mockup.agentName')}</div>
                      <div className="text-xs text-muted-foreground">&quot;{t('home.security.mockup.agentGreeting')}&quot;</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 rounded-xl bg-green-500/5 p-4 border border-green-500/10">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-500/10 text-green-600 dark:text-green-400">
                      <MessageCircle className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="text-sm font-medium">{t('home.security.mockup.customerName')}</div>
                      <div className="text-xs text-muted-foreground">&quot;{t('home.security.mockup.customerQuery')}&quot;</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 rounded-xl bg-muted/50 p-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-500/10 text-green-600 dark:text-green-400">
                      <Bot className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="text-sm font-medium">{t('home.security.mockup.agentName')}</div>
                      <div className="text-xs text-muted-foreground">&quot;{t('home.security.mockup.agentResponse')}&quot;</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 rounded-xl bg-muted/50 p-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                      <BarChart3 className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="text-sm font-medium">{t('home.security.mockup.leadCaptured')}</div>
                      <div className="text-xs text-muted-foreground">{t('home.security.mockup.leadDetails')}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════
          CTA SECTION
      ═══════════════════════════════════════════════ */}
      <section id="pricing" className="border-t bg-muted/30 py-24">
        <div className="mx-auto max-w-3xl px-4 text-center sm:px-6">
          <div className="inline-flex items-center rounded-full border border-green-500/20 bg-green-500/5 px-3 py-1 text-xs font-medium text-green-600 dark:text-green-400 mb-4">
            {t('home.cta.badge')}
          </div>
          <h2 className="text-3xl font-bold tracking-tight sm:text-4xl mb-4">
            {t('home.cta.title')}{' '}
            <span className="bg-gradient-to-r from-green-500 to-emerald-500 bg-clip-text text-transparent">
              {t('home.cta.titleAccent')}
            </span>
          </h2>
          <p className="mx-auto max-w-lg text-muted-foreground mb-10 leading-relaxed">
            {t('home.cta.description')}
          </p>

          <Link href="/register">
            <Button size="lg" className="px-10 bg-gradient-to-r from-green-500 to-emerald-600 text-white shadow-lg shadow-green-500/25 hover:shadow-xl hover:shadow-green-500/30 hover:scale-[1.02] transition-all border-0 text-base">
              <Sparkles className="mr-2 h-4 w-4" />
              {t('home.cta.button')}
            </Button>
          </Link>

          <p className="mt-4 text-xs text-muted-foreground">
            {t('home.cta.footer')}
          </p>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════
          FOOTER
      ═══════════════════════════════════════════════ */}
      <footer className="border-t py-8">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
            <div className="flex items-center gap-2">
              <div className="flex h-6 w-6 items-center justify-center rounded-md bg-gradient-to-br from-green-500 to-emerald-600 text-white text-xs font-bold">
                E
              </div>
              <span className="text-sm font-semibold">
                Enpi<span className="text-green-500">AI</span>
              </span>
            </div>
            <p className="text-xs text-muted-foreground">
              © {new Date().getFullYear()} WEBLIFETECH. {t('home.footer.legal')}
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
