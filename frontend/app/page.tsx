import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { ArrowRight, Bot, Shield, Zap } from 'lucide-react';

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col">
      {/* Nav */}
      <header className="sticky top-0 z-50 border-b bg-background/80 backdrop-blur-sm">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
          <span className="text-xl font-bold tracking-tight">
            Enpi<span className="text-primary">AI</span>
          </span>
          <div className="flex items-center gap-3">
            <Link href="/login">
              <Button variant="ghost" size="sm">
                Sign In
              </Button>
            </Link>
            <Link href="/register">
              <Button size="sm">
                Get Started <ArrowRight className="ml-1 h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <main className="flex flex-1 flex-col items-center justify-center px-4 text-center">
        <div className="mx-auto max-w-3xl space-y-8">
          <div className="inline-flex items-center rounded-full border bg-muted/50 px-4 py-1.5 text-sm text-muted-foreground">
            <Zap className="mr-2 h-3.5 w-3.5" />
            AI-Powered Business Automation
          </div>

          <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl lg:text-6xl">
            Your Intelligent
            <br />
            <span className="bg-gradient-to-r from-primary via-primary/70 to-primary bg-clip-text text-transparent">
              Workforce
            </span>
          </h1>

          <p className="mx-auto max-w-xl text-lg text-muted-foreground">
            Automate lead capture, customer support, scheduling, and wellness
            evaluations — all powered by AI agents that work 24/7 for your
            Herbalife business.
          </p>

          <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <Link href="/register">
              <Button size="lg" className="px-8">
                Start Free Trial <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
            <Link href="/login">
              <Button variant="outline" size="lg" className="px-8">
                Sign In
              </Button>
            </Link>
          </div>
        </div>

        {/* Feature Cards */}
        <div className="mx-auto mt-24 grid max-w-4xl gap-6 px-4 sm:grid-cols-3">
          <div className="rounded-xl border bg-card p-6 text-left shadow-sm transition-shadow hover:shadow-md">
            <Bot className="mb-3 h-8 w-8 text-primary" />
            <h3 className="font-semibold">AI Agents</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              Customizable agents that handle WhatsApp &amp; Telegram conversations
              automatically.
            </p>
          </div>
          <div className="rounded-xl border bg-card p-6 text-left shadow-sm transition-shadow hover:shadow-md">
            <Shield className="mb-3 h-8 w-8 text-primary" />
            <h3 className="font-semibold">Sovereign Data</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              End-to-end encryption for all customer data. Your keys, your
              data.
            </p>
          </div>
          <div className="rounded-xl border bg-card p-6 text-left shadow-sm transition-shadow hover:shadow-md">
            <Zap className="mb-3 h-8 w-8 text-primary" />
            <h3 className="font-semibold">Zero Friction</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              Wellness evaluations, CRM, and scheduling — all in one
              seamless platform.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t py-6 text-center text-sm text-muted-foreground">
        © {new Date().getFullYear()} WEBLIFETECH. All rights reserved.
      </footer>
    </div>
  );
}
