/**
 * Channels Service
 * Handles API calls for WhatsApp session management
 */
import apiClient from '@/lib/api-client';

export interface WhatsAppStatusResponse {
    connected: boolean;
    phone?: string | null;
    status?: string | null;
}

export interface WhatsAppQRResponse {
    qr?: string;
    success?: boolean;
    error?: string;
}

export interface ChannelActionResponse {
    success: boolean;
    message?: string;
    error?: string;
    session_id?: string;
}

export const channelsService = {
    /**
     * Initialize WhatsApp session (triggers QR generation)
     */
    async initWhatsApp(): Promise<ChannelActionResponse> {
        const { data } = await apiClient.post<ChannelActionResponse>('/channels/whatsapp/init');
        return data;
    },

    /**
     * Get WhatsApp QR code for scanning
     */
    async getWhatsAppQR(): Promise<WhatsAppQRResponse> {
        const { data } = await apiClient.get<WhatsAppQRResponse>('/channels/whatsapp/qr');
        return data;
    },

    /**
     * Get WhatsApp connection status
     */
    async getWhatsAppStatus(): Promise<WhatsAppStatusResponse> {
        const { data } = await apiClient.get<WhatsAppStatusResponse>('/channels/whatsapp/status');
        return data;
    },

    /**
     * Disconnect WhatsApp session
     */
    async disconnectWhatsApp(): Promise<ChannelActionResponse> {
        const { data } = await apiClient.post<ChannelActionResponse>('/channels/whatsapp/disconnect');
        return data;
    },
};

export default channelsService;
