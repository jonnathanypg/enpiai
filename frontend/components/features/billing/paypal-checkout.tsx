'use client';

import React, { useState } from 'react';
import { 
    PayPalButtons, 
    usePayPalScriptReducer,
    PayPalCardFieldsProvider,
    PayPalCardFieldsForm,
    PayPalCardFieldsButton,
    PayPalButtonsProps
} from "@paypal/react-paypal-js";
import { Loader2, AlertCircle, CreditCard } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import apiClient from '@/lib/api-client';
import { toast } from 'sonner';

interface PayPalCheckoutProps {
    planId: number;
    onSuccess?: (data: any) => void;
    onError?: (error: any) => void;
}

export const PayPalCheckout: React.FC<PayPalCheckoutProps> = ({ 
    planId, 
    onSuccess, 
    onError 
}) => {
    const [{ isPending, options }, dispatch] = usePayPalScriptReducer();
    const [config, setConfig] = useState<any>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [showCardFields, setShowCardFields] = useState(false);

    const fetchConfig = async () => {
        setLoading(true);
        setError(null);
        try {
            const { data } = await apiClient.post('/billing/subscribe', { plan_id: planId });
            setConfig(data);
            
            // Update PayPal Script Options based on the plan type
            const newOptions = {
                ...options,
                "client-id": data.client_id,
                "intent": data.type === 'order' ? 'capture' : 'subscription',
                "vault": data.type === 'subscription' ? 'true' : 'false',
                "components": "buttons,card-fields"
            };
            
            dispatch({
                type: "resetOptions",
                value: newOptions
            });
        } catch (err: any) {
            const msg = err.response?.data?.error || "Error initializing PayPal";
            setError(msg);
            toast.error(msg);
        } finally {
            setLoading(false);
        }
    };

    React.useEffect(() => {
        fetchConfig();
    }, [planId]);

    if (loading || isPending) {
        return (
            <div className="flex flex-col items-center justify-center p-8 space-y-4">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                <p className="text-sm text-muted-foreground">Initializing secure checkout...</p>
            </div>
        );
    }

    if (error) {
        return (
            <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
                <Button variant="outline" size="sm" onClick={fetchConfig} className="mt-2">
                    Retry
                </Button>
            </Alert>
        );
    }

    if (!config) return null;

    return (
        <div className="space-y-6 w-full max-w-md mx-auto">
            {/* Payment Method Selection */}
            <div className="flex flex-col space-y-4">
                <p className="text-sm font-medium text-center text-muted-foreground">
                    Pay securely with card or PayPal
                </p>

                {/* PayPal Buttons (Standard handles PayPal Login and basic Guest Checkout) */}
                <div className={showCardFields ? "hidden" : "block"}>
                    <PayPalButtons
                        style={{ 
                            layout: 'vertical',
                            shape: 'rect',
                            label: 'pay'
                        }}
                        createSubscription={(data, actions) => {
                            if (config.type === 'subscription') {
                                return actions.subscription.create({
                                    plan_id: config.paypal_plan_id,
                                    custom_id: String(config.distributor_id)
                                });
                            }
                            return "";
                        }}
                        createOrder={(data, actions) => {
                            if (config.type === 'order') {
                                return config.order_id;
                            }
                            return "";
                        }}
                        onApprove={async (data, actions) => {
                            if (config.type === 'subscription') {
                                toast.success("Subscription successful!");
                                if (onSuccess) onSuccess(data);
                                // Redirect or refresh
                                window.location.reload();
                            } else {
                                // Capture Order
                                try {
                                    const { data: captureData } = await apiClient.post('/billing/capture-order', {
                                        order_id: data.orderId,
                                        plan_id: planId
                                    });
                                    toast.success("Payment successful!");
                                    if (onSuccess) onSuccess(captureData);
                                    window.location.reload();
                                } catch (err) {
                                    toast.error("Error capturing payment");
                                }
                            }
                        }}
                        onError={(err) => {
                            console.error("PayPal Error:", err);
                            toast.error("PayPal execution error");
                            if (onError) onError(err);
                        }}
                    />
                </div>

                {/* Manual Card Fields Toggle (ACDC) */}
                <Button 
                    variant="outline" 
                    className="w-full"
                    onClick={() => setShowCardFields(!showCardFields)}
                >
                    <CreditCard className="mr-2 h-4 w-4" />
                    {showCardFields ? "Use other methods" : "Pay with Credit or Debit Card"}
                </Button>

                {showCardFields && (
                    <div className="p-4 border rounded-lg bg-card space-y-4">
                        <PayPalCardFieldsProvider
                            createOrder={async () => {
                                if (config.type === 'order') return config.order_id;
                                // Subscriptions via CardFields is more complex and usually 
                                // handled by the Standard PayPalButtons.
                                return "";
                            }}
                            onApprove={async (data) => {
                                if (config.type === 'order') {
                                    const { data: captureData } = await apiClient.post('/billing/capture-order', {
                                        order_id: data.orderId,
                                        plan_id: planId
                                    });
                                    toast.success("Payment successful!");
                                    if (onSuccess) onSuccess(captureData);
                                    window.location.reload();
                                }
                            }}
                        >
                            <PayPalCardFieldsForm />
                            <PayPalCardFieldsButton 
                                className="w-full mt-4 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2 rounded-md font-medium"
                                children="Pay Now"
                            />
                        </PayPalCardFieldsProvider>
                    </div>
                )}
            </div>
        </div>
    );
};
