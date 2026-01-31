/**
 * AdMob Service - Capacitor AdMob wrapper for iOS/Android
 */

import { AdMob, RewardAdPluginEvents } from '@capacitor-community/admob';
import type { AdMobRewardItem } from '@capacitor-community/admob';
import { Capacitor } from '@capacitor/core';
import type { PluginListenerHandle } from '@capacitor/core';

// Ad Unit IDs
const AD_UNITS = {
    android: {
        rewarded: 'ca-app-pub-2094089827700165/2603052881',
    },
    ios: {
        rewarded: 'ca-app-pub-2094089827700165/2934241282',
    },
    // Test IDs for development
    test: {
        rewarded: 'ca-app-pub-3940256099942544/5224354917', // Google's test rewarded ad
    }
};

// Get current platform ad unit
function getAdUnitId(type: 'rewarded'): string {
    const platform = Capacitor.getPlatform();

    // Use test ads during development
    if (import.meta.env.DEV) {
        return AD_UNITS.test[type];
    }

    if (platform === 'android') {
        return AD_UNITS.android[type];
    } else if (platform === 'ios') {
        return AD_UNITS.ios[type];
    }

    // Fallback to test for web
    return AD_UNITS.test[type];
}

let isInitialized = false;
let rewardedAdLoaded = false;

/**
 * Initialize AdMob SDK
 */
export async function initializeAdMob(): Promise<void> {
    if (isInitialized) return;

    const platform = Capacitor.getPlatform();
    if (platform === 'web') {
        console.log('AdMob: Running on web, using mock ads');
        isInitialized = true;
        return;
    }

    try {
        await AdMob.initialize({
            testingDevices: import.meta.env.DEV ? [] : [],
            initializeForTesting: import.meta.env.DEV,
        });

        isInitialized = true;
        console.log('✅ AdMob initialized');

        // Preload first rewarded ad
        await prepareRewardedAd();
    } catch (error) {
        console.error('❌ AdMob init error:', error);
    }
}

/**
 * Prepare (preload) a rewarded ad
 */
export async function prepareRewardedAd(): Promise<void> {
    const platform = Capacitor.getPlatform();
    if (platform === 'web') return;

    try {
        await AdMob.prepareRewardVideoAd({
            adId: getAdUnitId('rewarded'),
            isTesting: import.meta.env.DEV,
        });
        rewardedAdLoaded = true;
        console.log('✅ Rewarded ad prepared');
    } catch (error) {
        console.error('❌ Rewarded ad prepare error:', error);
        rewardedAdLoaded = false;
    }
}

/**
 * Show rewarded ad and return promise that resolves when user earns reward
 */
export function showRewardedAd(): Promise<AdMobRewardItem | null> {
    return new Promise(async (resolve) => {
        const platform = Capacitor.getPlatform();

        // Web fallback - simulate watching ad
        if (platform === 'web') {
            console.log('AdMob: Simulating rewarded ad on web...');
            // Simulate 3 second ad
            await new Promise(r => setTimeout(r, 3000));
            resolve({ type: 'coins', amount: 1 });
            return;
        }

        if (!rewardedAdLoaded) {
            console.log('Rewarded ad not loaded, preparing...');
            await prepareRewardedAd();

            if (!rewardedAdLoaded) {
                console.error('Failed to load rewarded ad');
                resolve(null);
                return;
            }
        }

        let rewardListener: PluginListenerHandle | null = null;
        let dismissListener: PluginListenerHandle | null = null;
        let failListener: PluginListenerHandle | null = null;

        // Listen for reward
        rewardListener = await AdMob.addListener(
            RewardAdPluginEvents.Rewarded,
            (reward: AdMobRewardItem) => {
                console.log('🎁 User earned reward:', reward);
                resolve(reward);
            }
        );

        // Listen for dismiss (no reward)
        dismissListener = await AdMob.addListener(
            RewardAdPluginEvents.Dismissed,
            () => {
                console.log('Ad dismissed');
                // Prepare next ad
                rewardedAdLoaded = false;
                prepareRewardedAd();
            }
        );

        // Listen for failure
        failListener = await AdMob.addListener(
            RewardAdPluginEvents.FailedToShow,
            (error: unknown) => {
                console.error('Failed to show ad:', error);
                resolve(null);
            }
        );

        try {
            await AdMob.showRewardVideoAd();
        } catch (error) {
            console.error('Show ad error:', error);
            resolve(null);
        }

        // Cleanup listeners after a timeout
        setTimeout(() => {
            rewardListener?.remove();
            dismissListener?.remove();
            failListener?.remove();
        }, 60000); // 1 minute timeout
    });
}

/**
 * Check if rewarded ad is ready
 */
export function isRewardedAdReady(): boolean {
    return rewardedAdLoaded;
}
