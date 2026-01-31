import { useState, useEffect } from 'react';
import { Capacitor } from '@capacitor/core';
import { showRewardedAd, isRewardedAdReady, prepareRewardedAd } from '../lib/admob';

interface AdWatchModalProps {
    isOpen: boolean;
    onClose: () => void;
    onReward: () => void;
}

export function AdWatchModal({ isOpen, onClose, onReward }: AdWatchModalProps) {
    const [timeLeft, setTimeLeft] = useState(5);
    const [canClose, setCanClose] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const isNative = Capacitor.isNativePlatform();

    useEffect(() => {
        if (isOpen && isNative) {
            // On native, show real ad immediately
            handleShowAd();
        } else if (isOpen && !isNative) {
            // On web, show fake ad with timer
            setTimeLeft(5);
            setCanClose(false);
            setError(null);
            const timer = setInterval(() => {
                setTimeLeft((prev) => {
                    if (prev <= 1) {
                        clearInterval(timer);
                        setCanClose(true);
                        return 0;
                    }
                    return prev - 1;
                });
            }, 1000);
            return () => clearInterval(timer);
        }
    }, [isOpen, isNative]);

    const handleShowAd = async () => {
        setIsLoading(true);
        setError(null);

        try {
            // Ensure ad is prepared
            if (!isRewardedAdReady()) {
                await prepareRewardedAd();
            }

            // Show the ad
            const reward = await showRewardedAd();

            if (reward) {
                // User earned reward
                onReward();
                onClose();
            } else {
                // User didn't complete or ad failed
                setError('Reklam tamamlanamadı. Tekrar deneyin.');
                setIsLoading(false);
            }
        } catch (err) {
            console.error('Ad error:', err);
            setError('Reklam yüklenemedi. Lütfen tekrar deneyin.');
            setIsLoading(false);
        }
    };

    const handleComplete = () => {
        if (canClose) {
            onReward();
            onClose();
        }
    };

    if (!isOpen) return null;

    // Native platform - show loading or error state
    if (isNative) {
        return (
            <div className="fixed inset-0 z-[60] bg-black/90 flex flex-col items-center justify-center p-8">
                {isLoading ? (
                    <div className="text-center">
                        <div className="size-12 border-3 border-primary border-t-transparent rounded-full animate-spin mb-4" />
                        <p className="text-white font-medium">Reklam yükleniyor...</p>
                    </div>
                ) : error ? (
                    <div className="text-center max-w-sm">
                        <span className="material-symbols-outlined text-6xl text-red-400 mb-4">error</span>
                        <p className="text-white font-medium mb-4">{error}</p>
                        <div className="flex gap-3">
                            <button
                                onClick={onClose}
                                className="flex-1 bg-white/10 text-white py-3 rounded-xl font-bold"
                            >
                                Kapat
                            </button>
                            <button
                                onClick={handleShowAd}
                                className="flex-1 bg-primary text-white py-3 rounded-xl font-bold"
                            >
                                Tekrar Dene
                            </button>
                        </div>
                    </div>
                ) : null}
            </div>
        );
    }

    // Web fallback - fake ad UI
    return (
        <div className="fixed inset-0 z-[60] bg-black flex flex-col items-center justify-center">
            <div className="w-full max-w-md aspect-[9/16] bg-gradient-to-br from-indigo-600 to-purple-700 relative flex items-center justify-center p-8">
                <div className="text-center">
                    <span className="material-symbols-outlined text-8xl text-white mb-4 animate-bounce">
                        shopping_bag
                    </span>
                    <h2 className="text-3xl font-bold text-white mb-2">Süper İndirimler!</h2>
                    <p className="text-white/80">Bu reklamı izleyerek premium tahminlere ücretsiz erişim kazanın.</p>
                </div>

                {/* Timer / Close Button */}
                <div className="absolute top-12 right-6">
                    {canClose ? (
                        <button
                            onClick={handleComplete}
                            className="bg-white/20 backdrop-blur-md text-white px-4 py-2 rounded-full font-bold flex items-center gap-2 hover:bg-white/30 transition-colors"
                        >
                            <span>Ödülü Al</span>
                            <span className="material-symbols-outlined text-sm">close</span>
                        </button>
                    ) : (
                        <div className="size-10 rounded-full border-2 border-white/30 flex items-center justify-center">
                            <span className="text-white font-bold">{timeLeft}</span>
                        </div>
                    )}
                </div>

                {/* Ad Badge */}
                <div className="absolute top-12 left-6 bg-black/40 px-2 py-1 rounded text-[10px] text-white/80 font-bold uppercase tracking-wider">
                    Reklam (Test)
                </div>
            </div>
        </div>
    );
}
