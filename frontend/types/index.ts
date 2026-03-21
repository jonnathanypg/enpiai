// API Response Types - Mapped 1:1 from Backend Models

// ========================
// Auth
// ========================
export interface User {
    id: number;
    email: string;
    name: string;
    role: 'admin' | 'super_admin';
    distributor_id: number | null;
    is_active: boolean;
    created_at: string | null;
    last_login: string | null;
}

export interface Distributor {
    id: number;
    name: string;
    herbalife_id: string | null;
    email: string;
    phone: string | null;
    country: string | null;
    city: string | null;
    language: string;
    subscription_tier: string;
    created_at: string;
}

export interface AuthResponse {
    data: {
        user: User;
        distributor?: Distributor;
        access_token: string;
        refresh_token: string;
    };
}

export interface MeResponse {
    data: User & { distributor?: Distributor };
}

// ========================
// Agents
// ========================
export interface AgentFeature {
    id: number;
    name: string;
    label: string;
    category: string;
    description: string;
    is_enabled: boolean;
    order: number;
}

export interface AgentConfig {
    id: number;
    name: string;
    description: string | null;
    agent_type: string;
    tone: string;
    objective: string;
    system_prompt: string | null;
    is_active: boolean;
    features: AgentFeature[];
}

// ========================
// CRM (Leads & Customers)
// ========================
export interface Lead {
    id: number;
    distributor_id: number;
    first_name: string | null;
    last_name: string | null;
    email: string | null;
    phone: string | null;
    source: string;
    status: 'new' | 'contacted' | 'qualified' | 'converted' | 'lost';
    score: number;
    metadata?: Record<string, any> | null;
    tags: string[];
    notes: string | null;
    created_at: string;
    updated_at: string;
}

export interface Customer {
    id: number;
    distributor_id: number;
    first_name: string;
    last_name: string | null;
    email: string | null;
    phone: string | null;
    status: string;
    created_at: string;
}

// ========================
// Wellness
// ========================
export interface WellnessEvaluation {
    id: number;
    distributor_id: number;
    lead_id: number | null;
    customer_id: number | null;
    age: number | null;
    gender: string | null;
    height_cm: number | null;
    weight_kg: number | null;
    bmi: number | null;
    primary_goal: string | null;
    created_at: string;
}

export interface Document {
    id: number;
    distributor_id: number;
    filename: string;
    original_filename: string;
    file_type: string;
    file_size: number;
    chunk_count: number;
    is_processed: boolean;
    description: string | null;
    tags: string[];
    created_at: string;
    processed_at: string | null;
}

// ========================
// Channels
// ========================
export interface Channel {
    id: number;
    distributor_id: number;
    channel_type: 'whatsapp' | 'telegram' | 'email' | 'web';
    name: string;
    status: 'active' | 'inactive' | 'error';
    config: Record<string, unknown>;
    created_at: string;
}

// ========================
// Conversations
// ========================
export interface Message {
    id: number;
    conversation_id: number;
    role: 'user' | 'assistant' | 'system' | 'tool';
    content: string;
    created_at: string;
}

export interface Conversation {
    id: number;
    distributor_id: number;
    contact_id: string | null;
    channel: string | null;
    messages: Message[];
    created_at: string;
}

// ========================
// Unified Identity (360)
// ========================
export interface UnifiedContact {
    lead: Lead | null;
    customer: Customer | null;
    conversations: Conversation[];
    appointments: Appointment[];
    evaluations: WellnessEvaluation[];
}

export interface Appointment {
    id: number;
    title: string;
    start_time: string;
    end_time: string;
    status: string;
    notes: string | null;
}

// ========================
// Admin / Plans
// ========================
export interface Plan {
    id: number;
    name: string;
    description: string | null;
    price_monthly: number;
    price_annual: number;
    currency: string;
    features: Record<string, unknown> | null;
    is_active: boolean;
    is_default: boolean;
}

export interface Subscription {
    id: number;
    distributor_id: number;
    plan_id: number;
    status: 'active' | 'trial' | 'past_due' | 'cancelled' | 'courtesy';
    interval: 'monthly' | 'annual';
    created_at: string;
}

export interface PlatformMetrics {
    total_distributors: number;
    active_subscriptions: number;
    total_leads: number;
    total_customers: number;
    total_conversations: number;
    total_messages: number;
    mrr: number;
}

export interface DistributorMetrics {
    total_leads: number;
    qualified_leads: number;
    total_customers: number;
    messages_today: number;
    active_conversations: number;
    conversion_rate: number;
}

// ========================
// Pagination
// ========================
export interface PaginatedResponse<T> {
    data: T[];
    pagination: {
        page: number;
        per_page: number;
        total: number;
        pages: number;
    };
}

// Generic API Response
export interface ApiResponse<T> {
    data: T;
    error?: string;
}
