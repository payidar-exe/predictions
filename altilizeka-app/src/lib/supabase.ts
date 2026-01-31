import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error('Missing Supabase environment variables');
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Types
export interface Profile {
    id: string;
    display_name: string | null;
    avatar_url: string | null;
    star_balance: number;
    created_at: string;
}

export interface Coupon {
    id: string;
    date: string;
    city: string;
    type: 'free' | 'premium';
    star_cost: number;
    title: string;
    subtitle: string | null;
    status?: 'pending' | 'won' | 'lost';
    winning_amount?: number;
    legs: CouponLeg[];
    created_at: string;
}

export interface CouponLeg {
    leg_no: number;
    race_time: string;
    race_info?: string;
    distance?: string;
    field_size: number;
    leg_result?: 'pending' | 'won' | 'lost';
    actual_winner?: string;
    horses: CouponHorse[];
}

export interface CouponHorse {
    program_no: number;
    horse_name: string;
    jockey_name?: string;
    last_6?: string;
    ai_score?: number; // 0-100
    is_banko: boolean;
    ai_note: string | null;
}

export interface StarPackage {
    id: string;
    name: string;
    stars: number;
    price_tl: number;
    ios_product_id: string;
    android_product_id: string;
    is_popular: boolean;
}
