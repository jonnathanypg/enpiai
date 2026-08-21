'use client';

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Bot, Play, Compass, X } from 'lucide-react';
import { useOnboardingStore } from '@/store/use-onboarding-store';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';

export function OnboardingWelcomeModal() {
    const { t } = useTranslation();
    const { hasSeenWelcome, setHasSeenWelcome, startTour } = useOnboardingStore();
    const [open, setOpen] = useState(false);

    useEffect(() => {
        // Show welcome modal if the user has not seen it yet
        if (!hasSeenWelcome) {
            // Delay slightly to allow page loading
            const timer = setTimeout(() => {
                setOpen(true);
            }, 1200);
            return () => clearTimeout(timer);
        }
    }, [hasSeenWelcome]);

    const handleStartTour = () => {
        setOpen(false);
        setHasSeenWelcome(true);
        // Start tour after a brief delay to let modal closing transition finish
        setTimeout(() => {
            startTour(0);
        }, 300);
    };

    const handleDismiss = () => {
        setOpen(false);
        setHasSeenWelcome(true);
    };

    return (
        <Dialog open={open} onOpenChange={(isOpen) => {
            if (!isOpen) handleDismiss();
        }}>
            <DialogContent className="w-[calc(100%-2rem)] max-w-[540px] sm:w-full sm:max-w-[540px] p-0 overflow-hidden border border-slate-200 dark:border-zinc-800 !bg-white dark:!bg-zinc-950 !opacity-100 shadow-2xl rounded-2xl [&_[data-slot=dialog-close]]:rounded-full [&_[data-slot=dialog-close]]:bg-black/10 [&_[data-slot=dialog-close]]:hover:bg-black/20 [&_[data-slot=dialog-close]]:text-white/80 [&_[data-slot=dialog-close]]:hover:text-white [&_[data-slot=dialog-close]]:p-1.5 [&_[data-slot=dialog-close]]:opacity-100 [&_[data-slot=dialog-close]]:top-5 [&_[data-slot=dialog-close]]:right-5">
                {/* Visual Header with Premium Wellness Gradient */}
                <div className="relative overflow-hidden pt-6 pb-5 px-6 text-white h-36 flex flex-col justify-end bg-gradient-to-br from-emerald-600 via-teal-600 to-green-500">
                    <div className="absolute -right-10 -top-10 h-40 w-40 rounded-full bg-white/10 blur-2xl" />
                    <div className="absolute -left-10 -bottom-10 h-32 w-32 rounded-full bg-green-400/20 blur-2xl" />

                    <div className="relative z-10 flex items-start gap-3 w-full">
                        <div className="bg-white/20 p-2.5 rounded-xl border border-white/20 backdrop-blur-md shadow-inner shrink-0">
                            <Bot className="h-6 w-6 text-white" />
                        </div>
                        <div className="min-w-0 flex-1">
                            <span className="text-xs font-semibold uppercase tracking-wider text-emerald-200">EnpiAI Platform</span>
                            <h2 className="text-2xl font-extrabold leading-tight text-white mt-0.5 break-words">
                                {t('onboarding.welcomeTitle')}
                            </h2>
                        </div>
                    </div>
                </div>

                {/* Content Area */}
                <div className="p-6 space-y-5">
                    <div className="space-y-1.5">
                        <h3 className="text-lg font-bold text-foreground">
                            {t('onboarding.welcomeSubtitle')}
                        </h3>
                        <p className="text-sm text-muted-foreground leading-relaxed">
                            {t('onboarding.welcomeDesc')}
                        </p>
                    </div>

                    {/* Features overview */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-xs">
                        <div className="flex gap-2.5 p-3 rounded-xl border bg-muted/30">
                            <span className="text-lg shrink-0">⚙️</span>
                            <div className="min-w-0 flex-1">
                                <h4 className="font-semibold text-foreground">{t('onboarding.stepProfile')}</h4>
                                <p className="text-muted-foreground mt-0.5 leading-relaxed">{t('onboarding.stepProfileDesc')}</p>
                            </div>
                        </div>
                        <div className="flex gap-2.5 p-3 rounded-xl border bg-muted/30">
                            <span className="text-lg shrink-0">🤖</span>
                            <div className="min-w-0 flex-1">
                                <h4 className="font-semibold text-foreground">{t('onboarding.stepAgents')}</h4>
                                <p className="text-muted-foreground mt-0.5 leading-relaxed">{t('onboarding.stepAgentsDesc')}</p>
                            </div>
                        </div>
                        <div className="flex gap-2.5 p-3 rounded-xl border bg-muted/30">
                            <span className="text-lg shrink-0">💬</span>
                            <div className="min-w-0 flex-1">
                                <h4 className="font-semibold text-foreground">{t('onboarding.stepChannels')}</h4>
                                <p className="text-muted-foreground mt-0.5 leading-relaxed">{t('onboarding.stepChannelsDesc')}</p>
                            </div>
                        </div>
                        <div className="flex gap-2.5 p-3 rounded-xl border bg-muted/30">
                            <span className="text-lg shrink-0">🌿</span>
                            <div className="min-w-0 flex-1">
                                <h4 className="font-semibold text-foreground">{t('onboarding.stepCoach')}</h4>
                                <p className="text-muted-foreground mt-0.5 leading-relaxed">{t('onboarding.stepCoachDesc')}</p>
                            </div>
                        </div>
                    </div>

                    {/* Footer Actions */}
                    <div className="flex flex-col sm:flex-row gap-2.5 pt-2">
                        <Button 
                            onClick={handleStartTour} 
                            className="w-full sm:w-auto sm:flex-1 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-semibold shadow-md shadow-emerald-500/10 h-11 rounded-xl transition-all duration-300 hover:scale-[1.02]"
                        >
                            <Play className="h-4 w-4 mr-2" />
                            {t('onboarding.startTour')}
                        </Button>
                        <Button 
                            onClick={handleDismiss} 
                            variant="outline" 
                            className="w-full sm:w-auto sm:flex-1 border-border/80 hover:bg-muted/50 h-11 rounded-xl"
                        >
                            <Compass className="h-4 w-4 mr-2 text-muted-foreground" />
                            {t('onboarding.exploreOnOwn')}
                        </Button>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
}
