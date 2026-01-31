import { create } from 'zustand';
import { supabase } from '../lib/supabase';
import type { Profile, Coupon } from '../lib/supabase';

interface AuthState {
    user: Profile | null;
    isLoading: boolean;
    isAuthenticated: boolean;
    signIn: (email: string, password: string) => Promise<void>;
    signUp: (email: string, password: string, displayName: string) => Promise<void>;
    signOut: () => Promise<void>;
    fetchProfile: () => Promise<void>;
    updateStarBalance: (delta: number) => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
    user: null,
    isLoading: true,
    isAuthenticated: false,

    signIn: async (email, password) => {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
        await get().fetchProfile();
    },

    signUp: async (email, password, displayName) => {
        const { data, error } = await supabase.auth.signUp({ email, password });
        if (error) throw error;

        // Create profile immediately if user is returned
        if (data.user) {
            await supabase.from('profiles').insert({
                id: data.user.id,
                display_name: displayName,
                star_balance: 50, // Welcome bonus
            });
        }
        await get().fetchProfile();
    },

    signOut: async () => {
        await supabase.auth.signOut();
        set({ user: null, isAuthenticated: false });
    },

    fetchProfile: async () => {
        set({ isLoading: true });
        try {
            const { data: { user } } = await supabase.auth.getUser();

            if (user) {
                let { data: profile, error: _profileError } = await supabase
                    .from('profiles')
                    .select('*')
                    .eq('id', user.id)
                    .single();

                // 1. Self-healing: Create profile if missing
                if (!profile) {
                    const fallbackName = user.user_metadata?.display_name || user.email?.split('@')[0] || 'Kullanıcı';
                    console.warn('Profile missing, creating fallback...');
                    const { data: newProfile, error: createError } = await supabase
                        .from('profiles')
                        .insert({
                            id: user.id,
                            display_name: fallbackName,
                            star_balance: 50,
                            avatar_url: null
                        })
                        .select()
                        .single();

                    if (!createError && newProfile) {
                        profile = newProfile;
                    } else {
                        // Temporary fallback object if insert fails
                        profile = {
                            id: user.id,
                            display_name: fallbackName,
                            star_balance: 50,
                            avatar_url: null,
                            created_at: new Date().toISOString(),
                            updated_at: new Date().toISOString()
                        } as Profile;
                    }
                }

                // 2. Fix missing name: If profile exists but name is empty/null which causes 'Misafir'
                if (profile && !profile.display_name) {
                    const fallbackName = user.user_metadata?.display_name || user.email?.split('@')[0] || 'Kullanıcı';
                    profile.display_name = fallbackName;
                    // Try to update DB in background
                    supabase.from('profiles').update({ display_name: fallbackName }).eq('id', user.id).then(({ error }) => {
                        if (error) console.error('Failed to auto-fix missing display_name:', error);
                    });
                }

                // Also fetch purchased coupons
                const { data: purchases } = await supabase
                    .from('user_coupons')
                    .select('coupon_id')
                    .eq('user_id', user.id);

                const purchasedIds = purchases?.map(p => p.coupon_id) || [];
                useCouponStore.getState().setPurchasedCoupons(purchasedIds);

                set({ user: profile, isAuthenticated: true, isLoading: false });
            } else {
                set({ user: null, isAuthenticated: false, isLoading: false });
                useCouponStore.getState().setPurchasedCoupons([]);
            }
        } catch (err) {
            console.error('Fetch profile error:', err);
            set({ user: null, isAuthenticated: false, isLoading: false });
        }
    },

    updateStarBalance: (delta) => {
        const currentUser = get().user;
        if (currentUser) {
            set({ user: { ...currentUser, star_balance: currentUser.star_balance + delta } });
        }
    },
}));

// Coupon Store
interface CouponState {
    coupons: Coupon[];
    isLoading: boolean;
    fetchTodayCoupons: () => Promise<void>;
    purchasedCouponIds: string[];
    addPurchasedCoupon: (couponId: string) => void;
    setPurchasedCoupons: (ids: string[]) => void;
}

export const useCouponStore = create<CouponState>((set, get) => ({
    coupons: [],
    isLoading: false,
    purchasedCouponIds: [],

    fetchTodayCoupons: async () => {
        set({ isLoading: true });
        const today = new Date().toISOString().split('T')[0];

        const { data } = await supabase
            .from('coupons')
            .select('*')
            .eq('date', today)
            .order('created_at', { ascending: false });

        set({ coupons: data || [], isLoading: false });
    },

    addPurchasedCoupon: (couponId) => {
        set({ purchasedCouponIds: [...get().purchasedCouponIds, couponId] });
    },

    setPurchasedCoupons: (ids) => {
        set({ purchasedCouponIds: ids });
    },
}));
