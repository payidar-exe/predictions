import { Purchases, LOG_LEVEL } from '@revenuecat/purchases-capacitor';
import type { PurchasesPackage } from '@revenuecat/purchases-capacitor';
import { Capacitor } from '@capacitor/core';
import { useAuthStore } from '../stores';

const REVENUECAT_API_KEYS = {
    apple: import.meta.env.VITE_REVENUECAT_APPLE_KEY || 'goog_placeholder',
    google: import.meta.env.VITE_REVENUECAT_GOOGLE_KEY || 'goog_placeholder',
};

export const initializeRevenueCat = async () => {
    if (!Capacitor.isNativePlatform()) {
        console.log('RevenueCat: Skipping initialization on web');
        return;
    }

    try {
        await Purchases.setLogLevel({ level: LOG_LEVEL.DEBUG });

        const platform = Capacitor.getPlatform();
        const apiKey = platform === 'ios' ? REVENUECAT_API_KEYS.apple : REVENUECAT_API_KEYS.google;

        await Purchases.configure({
            apiKey: apiKey,
            appUserID: useAuthStore.getState().user?.id || undefined,
        });

        console.log('✅ RevenueCat initialized');
    } catch (error) {
        console.error('❌ RevenueCat initialization error:', error);
    }
};

export const getOfferings = async () => {
    if (!Capacitor.isNativePlatform()) return null;

    try {
        const offerings = await Purchases.getOfferings();
        return offerings.current;
    } catch (error) {
        console.error('❌ Error fetching offerings:', error);
        return null;
    }
};

export const purchasePackage = async (rcPackage: PurchasesPackage) => {
    try {
        const result = await Purchases.purchasePackage({ aPackage: rcPackage });

        // Purchase successful
        if (typeof result.customerInfo.entitlements.active !== 'undefined') {
            return true;
        }
        return false;
    } catch (error: any) {
        if (!error.userCancelled) {
            console.error('❌ Purchase error:', error);
        }
        return false;
    }
};

export const restorePurchases = async () => {
    try {
        const customerInfo = await Purchases.restorePurchases();
        return customerInfo;
    } catch (error) {
        console.error('❌ Restore error:', error);
        return null;
    }
};
