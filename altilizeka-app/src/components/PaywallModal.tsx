import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores';
import { supabase } from '../lib/supabase';

interface PaywallModalProps {
    isOpen: boolean;
    onClose: () => void;
    couponId: string;
    couponTitle: string;
    starCost: number;
    onSuccess: () => void;
}

export function PaywallModal({ isOpen, onClose, couponId, couponTitle, starCost, onSuccess }: PaywallModalProps) {
    const user = useAuthStore((s) => s.user);
    const updateStarBalance = useAuthStore((s) => s.updateStarBalance);
    const [isProcessing, setIsProcessing] = useState(false);
    const navigate = useNavigate();

    const canAfford = (user?.star_balance ?? 0) >= starCost;
    const remainingBalance = (user?.star_balance ?? 0) - starCost;

    const handlePurchase = async () => {
        if (!user || !canAfford) return;

        setIsProcessing(true);
        try {
            // Deduct stars from profile
            const { error: updateError } = await supabase
                .from('profiles')
                .update({ star_balance: remainingBalance })
                .eq('id', user.id);

            if (updateError) throw updateError;

            // Record transaction
            await supabase.from('star_transactions').insert({
                user_id: user.id,
                amount: -starCost,
                type: 'spend',
                description: `${couponTitle} kuponu`,
            });

            // Record purchase
            await supabase.from('user_coupons').insert({
                user_id: user.id,
                coupon_id: couponId,
            });

            // Update local state
            updateStarBalance(-starCost);
            onSuccess();
            onClose();
        } catch (error) {
            console.error('Purchase failed:', error);
        } finally {
            setIsProcessing(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 bg-black/60 ios-blur flex items-end justify-center">
            <div className="w-full max-w-md bg-background-dark rounded-t-2xl shadow-2xl border-t border-white/10 flex flex-col items-stretch animate-in slide-in-from-bottom duration-300">
                {/* Handle */}
                <button onClick={onClose} className="flex h-6 w-full items-center justify-center pt-2">
                    <div className="h-1.5 w-12 rounded-full bg-white/20" />
                </button>

                {/* Header */}
                <div className="pt-2">
                    <h4 className="text-primary text-sm font-bold leading-normal tracking-[0.05em] px-4 py-2 text-center uppercase">
                        {canAfford ? 'Kupon Satın Alma Onayı' : 'Yetersiz Bakiye'}
                    </h4>
                </div>

                {/* Content */}
                <div className="px-6 py-4 flex flex-col items-center">
                    {/* Icon */}
                    <div className={`w-20 h-20 rounded-full flex items-center justify-center mb-6 border ${canAfford
                            ? 'bg-primary/10 border-primary/20'
                            : 'bg-red-500/10 border-red-500/20'
                        }`}>
                        <span
                            className={`material-symbols-outlined text-5xl ${canAfford ? 'text-primary' : 'text-red-400'}`}
                            style={{ fontVariationSettings: "'FILL' 1" }}
                        >
                            {canAfford ? 'stars' : 'error'}
                        </span>
                    </div>

                    {/* Title */}
                    <h3 className="text-white tracking-tight text-2xl font-bold leading-tight text-center pb-6">
                        {canAfford ? (
                            <>
                                Bu kuponu <span className="text-primary">{starCost} Yıldız</span> karşılığında açmak istiyor musunuz?
                            </>
                        ) : (
                            <>
                                <span className="text-red-400">{starCost - (user?.star_balance ?? 0)} Yıldız</span> daha gerekiyor
                            </>
                        )}
                    </h3>

                    {/* Balance Card */}
                    <div className="w-full bg-card-dark border border-white/5 rounded-2xl p-4 mb-8 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="bg-accent-gold/20 p-2 rounded-lg">
                                <span className="material-symbols-outlined text-accent-gold text-2xl">account_balance_wallet</span>
                            </div>
                            <div>
                                <p className="text-white/50 text-xs font-medium uppercase tracking-wider">Mevcut Bakiyeniz</p>
                                <p className="text-white text-lg font-bold leading-none">{user?.star_balance ?? 0} Yıldız</p>
                            </div>
                        </div>
                        <div className="h-8 w-0.5 bg-white/10" />
                        <div className="text-right">
                            <p className="text-white/50 text-xs font-medium uppercase tracking-wider">İşlem Sonrası</p>
                            <p className={`text-lg font-bold leading-none ${canAfford ? 'text-primary' : 'text-red-500'}`}>
                                {canAfford ? `${remainingBalance} Yıldız` : 'Yetersiz'}
                            </p>
                        </div>
                    </div>

                    {/* Buttons */}
                    <div className="flex flex-col w-full gap-3 pb-8">
                        {canAfford ? (
                            <button
                                onClick={handlePurchase}
                                disabled={isProcessing}
                                className="flex items-center justify-center rounded-xl h-14 bg-primary hover:bg-primary/90 disabled:opacity-50 transition-colors text-white text-lg font-bold w-full shadow-lg shadow-primary/20"
                            >
                                {isProcessing ? (
                                    <div className="size-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                ) : (
                                    'Kuponu Aç'
                                )}
                            </button>
                        ) : (
                            <button
                                onClick={() => {
                                    onClose();
                                    navigate('/stars');
                                }}
                                className="flex items-center justify-center rounded-xl h-14 bg-accent-gold hover:bg-accent-gold/90 transition-colors text-background-dark text-lg font-bold w-full"
                            >
                                Yıldız Satın Al
                            </button>
                        )}
                        <button
                            onClick={onClose}
                            className="flex items-center justify-center rounded-xl h-14 bg-transparent hover:bg-white/5 transition-colors text-white/60 text-base font-semibold w-full"
                        >
                            Vazgeç
                        </button>
                    </div>

                    {/* Footer Note */}
                    {canAfford && (
                        <p className="text-white/30 text-[11px] text-center px-8 pb-4">
                            Satın alınan kuponlar 'Kuponlarım' sekmesine eklenir ve dilediğiniz zaman erişilebilir kalır.
                        </p>
                    )}
                </div>
            </div>
        </div>
    );
}
