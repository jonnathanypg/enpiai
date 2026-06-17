'use client';
 
import React, { useState, useEffect } from 'react';
import { PayPalScriptProvider, PayPalButtons, usePayPalScriptReducer } from "@paypal/react-paypal-js";
import { Loader2, AlertCircle, CreditCard } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { useTranslation } from 'react-i18next';
import apiClient from '@/lib/api-client';
import { toast } from 'sonner';

interface PayPalCheckoutProps {
    planId: number;
    onSuccess?: (data: any) => void;
    onError?: (error: any) => void;
}

// ─────────────────────────────────────────────────────────────────────────────
// Inner component: renders SUBSCRIPTION buttons
// ─────────────────────────────────────────────────────────────────────────────
const SubscriptionButtons: React.FC<{
    config: any;
    onSuccess?: (data: any) => void;
    onError?: (error: any) => void;
}> = ({ config, onSuccess, onError }) => {
    const { t } = useTranslation();
    const [{ isPending, isRejected }] = usePayPalScriptReducer();

    if (isPending) {
        return (
            <div className="flex flex-col items-center justify-center p-6 space-y-3">
                <Loader2 className="h-7 w-7 animate-spin text-primary" />
                <p className="text-sm text-gray-600 text-center">{t('subscribe.checkout.loadingPayPal')}</p>
            </div>
        );
    }

    if (isRejected) {
        return (
            <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>{t('subscribe.checkout.scriptErrorTitle')}</AlertTitle>
                <AlertDescription>
                    {t('subscribe.checkout.scriptErrorDesc')}
                </AlertDescription>
            </Alert>
        );
    }

    return (
        <PayPalButtons
            style={{ layout: 'vertical', shape: 'rect', label: 'subscribe', height: 48 }}
            // createSubscription is ONLY used when intent=subscription
            createSubscription={(data, actions) => {
                return actions.subscription.create({
                    plan_id: config.paypal_plan_id,
                    custom_id: String(config.distributor_id),
                });
            }}
            onApprove={async (data) => {
                try {
                    // Try to verify and activate the subscription on the backend instantly
                    await apiClient.post('/billing/verify-subscription', {
                        subscription_id: data.subscriptionID
                    });
                    toast.success(t('subscribe.checkout.successSubscription'));
                } catch (err) {
                    console.error("Direct subscription verification failed:", err);
                    // Fallback to success toast anyway, since webhook might activate it shortly
                    toast.success(t('subscribe.checkout.successSubscription'));
                }
                if (onSuccess) onSuccess(data);
                window.location.href = '/dashboard';
            }}
            onError={(err) => {
                console.error("PayPal Subscription Error:", err);
                toast.error(t('subscribe.checkout.errorSubscription'));
                if (onError) onError(err);
            }}
            onCancel={() => {
                toast.info(t('subscribe.checkout.subscriptionCancelled'));
            }}
        />
    );
};

// ─────────────────────────────────────────────────────────────────────────────
// Inner component: renders ONE-TIME ORDER buttons (credit blocks)
// ─────────────────────────────────────────────────────────────────────────────
const OrderButtons: React.FC<{
    config: any;
    planId: number;
    onSuccess?: (data: any) => void;
    onError?: (error: any) => void;
}> = ({ config, planId, onSuccess, onError }) => {
    const { t } = useTranslation();
    const [{ isPending, isRejected }] = usePayPalScriptReducer();

    if (isPending) {
        return (
            <div className="flex flex-col items-center justify-center p-6 space-y-3">
                <Loader2 className="h-7 w-7 animate-spin text-primary" />
                <p className="text-sm text-gray-600 text-center">{t('subscribe.checkout.loadingPayPal')}</p>
            </div>
        );
    }

    if (isRejected) {
        return (
            <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>{t('subscribe.checkout.scriptErrorTitle')}</AlertTitle>
                <AlertDescription>
                    {t('subscribe.checkout.scriptErrorDesc')}
                </AlertDescription>
            </Alert>
        );
    }

    return (
        <PayPalButtons
            style={{ layout: 'vertical', shape: 'rect', label: 'pay', height: 48 }}
            // createOrder is ONLY used when intent=capture (one-time payment)
            createOrder={() => {
                // The order_id was already created by the backend; return it directly.
                // PayPal accepts either a new order via actions.order.create() or an existing order ID.
                return Promise.resolve(config.order_id);
            }}
            onApprove={async (data) => {
                try {
                    const { data: captureData } = await apiClient.post('/billing/capture-order', {
                        order_id: data.orderID,
                        plan_id: planId,
                    });
                    toast.success(t('subscribe.checkout.successOrder'));
                    if (onSuccess) onSuccess(captureData);
                    window.location.reload();
                } catch {
                    toast.error(t('subscribe.checkout.errorCapture'));
                }
            }}
            onError={(err) => {
                console.error("PayPal Order Error:", err);
                toast.error(t('subscribe.checkout.errorOrder'));
                if (onError) onError(err);
            }}
            onCancel={() => {
                toast.info(t('subscribe.checkout.cancelled'));
            }}
        />
    );
};

// ─────────────────────────────────────────────────────────────────────────────
// Main Exported Component
// ─────────────────────────────────────────────────────────────────────────────
export const PayPalCheckout: React.FC<PayPalCheckoutProps> = ({
    planId,
    onSuccess,
    onError,
}) => {
    const { t, i18n } = useTranslation();
    const currentLang = i18n.language || 'en';
    const [config, setConfig] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const getPayPalLocale = (lang: string) => {
        if (lang.startsWith('es')) return 'es_ES';
        if (lang.startsWith('pt')) return 'pt_BR';
        return 'en_US';
    };

    const fetchConfig = async () => {
        setLoading(true);
        setError(null);
        try {
            const { data } = await apiClient.post('/billing/subscribe', { plan_id: planId });
            setConfig(data);
        } catch (err: any) {
            const msg = err.response?.data?.error || t('subscribe.subscriptionError');
            setError(msg);
            toast.error(msg);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchConfig();
    }, [planId]);

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center p-8 space-y-4">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                <p className="text-sm text-gray-600 text-center">{t('subscribe.checkout.preparingCheckout')}</p>
            </div>
        );
    }

    if (error) {
        return (
            <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>{t('subscribe.checkout.checkoutErrorTitle')}</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
                <Button variant="outline" size="sm" onClick={fetchConfig} className="mt-3">
                    {t('subscribe.checkout.tryAgain')}
                </Button>
            </Alert>
        );
    }

    if (!config || !config.client_id) {
        return (
            <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>{t('subscribe.checkout.configErrorTitle')}</AlertTitle>
                <AlertDescription>
                    {t('subscribe.checkout.configErrorDesc')}
                </AlertDescription>
            </Alert>
        );
    }

    const isSubscription = config.type === 'subscription';

    /*
     * IMPORTANT — SDK options:
     * - For subscriptions: intent="subscription", vault=true (boolean, not string!)
     * - For one-time orders: intent="capture", vault=false
     * - "vault" must be a boolean in the options object for the SDK to parse it correctly.
     * - "locale" determines button rendering language.
     * - Do NOT mix createSubscription and createOrder on the same PayPalButtons instance.
     */
    const sdkOptions = isSubscription
        ? {
              clientId: config.client_id,
              intent: 'subscription' as const,
              vault: true,
              components: 'buttons',
              locale: getPayPalLocale(currentLang),
          }
        : {
              clientId: config.client_id,
              intent: 'capture' as const,
              vault: false,
              components: 'buttons',
              locale: getPayPalLocale(currentLang),
          };

    return (
        <div className="space-y-5 w-full bg-white text-black">
            <div className="flex items-center gap-2 text-sm text-gray-600">
                <CreditCard className="h-4 w-4 shrink-0" />
                <span>
                    {isSubscription
                        ? t('subscribe.checkout.recurringPayment')
                        : t('subscribe.checkout.oneTimePayment')}
                </span>
            </div>

            {/* 
             * Each PayPalScriptProvider is mounted with fully resolved, final options.
             * Mounting it here (inside the component, after config is known) prevents
             * race conditions and "PENDING" client-id issues from a parent provider.
             */}
            <div className="w-full min-h-[150px] flex flex-col justify-center [&_iframe]:!bg-transparent">
                <PayPalScriptProvider options={sdkOptions}>
                    {isSubscription ? (
                        <SubscriptionButtons
                            config={config}
                            onSuccess={onSuccess}
                            onError={onError}
                        />
                    ) : (
                        <OrderButtons
                            config={config}
                            planId={planId}
                            onSuccess={onSuccess}
                            onError={onError}
                        />
                    )}
                </PayPalScriptProvider>
            </div>

            <p className="text-[11px] text-center text-gray-500 leading-relaxed px-2">
                {isSubscription 
                    ? t('subscribe.checkout.recurringNote')
                    : t('subscribe.checkout.oneTimeNote')}
            </p>
        </div>
    );
};
