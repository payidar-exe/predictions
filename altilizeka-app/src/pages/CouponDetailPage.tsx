import { useEffect, useState } from 'react';
import { useParams, Link, useSearchParams } from 'react-router-dom';
import { supabase } from '../lib/supabase';
import type { Coupon } from '../lib/supabase';
import { useAuthStore, useCouponStore } from '../stores';

export function CouponDetailPage() {
    const { id } = useParams<{ id: string }>();
    const [searchParams] = useSearchParams();
    const [coupon, setCoupon] = useState<Coupon | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [showUnlockModal, setShowUnlockModal] = useState(searchParams.get('unlock') === 'true');

    const user = useAuthStore((s) => s.user);
    const updateStarBalance = useAuthStore((s) => s.updateStarBalance);
    const purchasedCouponIds = useCouponStore((s) => s.purchasedCouponIds);
    const addPurchasedCoupon = useCouponStore((s) => s.addPurchasedCoupon);

    const isPurchased = purchasedCouponIds.includes(id || '') || coupon?.type === 'free';
    const canAfford = (user?.star_balance ?? 0) >= (coupon?.star_cost ?? 0);

    useEffect(() => {
        const fetchCoupon = async () => {
            if (!id) return;
            const { data } = await supabase.from('coupons').select('*').eq('id', id).single();
            setCoupon(data);
            setIsLoading(false);
        };
        fetchCoupon();
    }, [id]);

    const handleUnlock = async () => {
        if (!coupon || !user || !canAfford) return;

        try {
            const { error: balanceError } = await supabase
                .from('profiles')
                .update({ star_balance: user.star_balance - coupon.star_cost })
                .eq('id', user.id);
            if (balanceError) throw balanceError;

            await supabase.from('star_transactions').insert({
                user_id: user.id,
                amount: -coupon.star_cost,
                type: 'spend',
                description: `${coupon.title} kuponu`,
            });

            const { error: purchaseError } = await supabase.from('user_coupons').insert({
                user_id: user.id,
                coupon_id: coupon.id,
            });
            if (purchaseError) throw purchaseError;

            updateStarBalance(-coupon.star_cost);
            addPurchasedCoupon(coupon.id);
            setShowUnlockModal(false);
        } catch (error) {
            console.error('Unlock failed:', error);
            alert('Kupon açılırken bir hata oluştu.');
        }
    };

    if (isLoading) return <div className="min-h-screen bg-background-dark flex items-center justify-center"><div className="size-8 border-2 border-primary border-t-transparent rounded-full animate-spin" /></div>;
    if (!coupon) return <div className="min-h-screen bg-background-dark flex items-center justify-center text-white">Kupon bulunamadı.</div>;

    return (
        <div className="min-h-screen bg-background-dark text-white font-sans">
            {/* Sticky Header */}
            <nav className="sticky top-0 z-50 bg-background-dark/95 backdrop-blur-xl border-b border-white/5 safe-area-top">
                <div className="flex items-center justify-between px-4 py-3">
                    <Link to="/" className="flex items-center justify-center size-10 rounded-full hover:bg-white/10 transition-colors">
                        <span className="material-symbols-outlined text-white">arrow_back_ios_new</span>
                    </Link>
                    <div className="flex flex-col items-center">
                        <span className="text-[10px] uppercase tracking-[0.2em] text-primary font-bold">KAHİN AI</span>
                        <h1 className="text-white text-base font-bold tracking-tight">Kupon Detayı</h1>
                    </div>
                    <div className="flex items-center justify-center size-10">
                        <div className="flex items-center gap-1 bg-white/5 px-2 py-1 rounded-full border border-white/10">
                            <span className="material-symbols-outlined text-accent-gold text-xs" style={{ fontVariationSettings: "'FILL' 1" }}>stars</span>
                            <span className="text-accent-gold text-xs font-bold">{user?.star_balance ?? 0}</span>
                        </div>
                    </div>
                </div>
            </nav>

            <main className="max-w-md mx-auto pb-24 px-4 pt-6">
                {/* Coupon Info Card */}
                <div className="bg-card-dark border border-white/5 rounded-2xl p-6 mb-8 relative overflow-hidden shadow-xl">
                    <div className="absolute top-0 right-0 p-4 opacity-10">
                        <span className="material-symbols-outlined text-6xl text-primary">analytics</span>
                    </div>
                    <div className="relative z-10">
                        <div className="flex items-center gap-2 mb-2">
                            <div className="bg-primary/20 text-primary border border-primary/20 text-[10px] font-bold px-2 py-0.5 rounded uppercase">
                                {coupon.city}
                            </div>
                            <span className="text-gray-500 text-xs">•</span>
                            <span className="text-gray-400 text-xs font-medium">{coupon.date}</span>
                        </div>
                        <h2 className="text-2xl font-extrabold text-white mb-1">{coupon.title}</h2>
                        <p className="text-primary text-xs font-bold uppercase tracking-widest">{coupon.subtitle}</p>
                    </div>
                </div>

                {/* Locked State */}
                {!isPurchased && (
                    <div className="bg-gradient-to-b from-card-dark to-black/40 border border-white/5 rounded-2xl p-8 flex flex-col items-center text-center shadow-lg">
                        <div className="size-20 bg-accent-gold/10 rounded-full flex items-center justify-center mb-6 border border-accent-gold/20 shadow-[0_0_30px_rgba(255,215,0,0.1)]">
                            <span className="material-symbols-outlined text-accent-gold text-4xl" style={{ fontVariationSettings: "'FILL' 1" }}>lock</span>
                        </div>
                        <h3 className="text-xl font-bold text-white mb-2">Profesyonel Analiz</h3>
                        <p className="text-gray-400 text-sm mb-8 leading-relaxed">
                            Bu analizde jokey performansları, son 6 yarış istatistikleri ve Kahin AI'nın özel notları bulunmaktadır.
                        </p>
                        <button
                            onClick={() => setShowUnlockModal(true)}
                            className="w-full bg-accent-gold hover:bg-accent-gold/90 text-background-dark py-4 rounded-xl font-bold text-lg shadow-lg flex items-center justify-center gap-2 transition-transform active:scale-95"
                        >
                            <span className="material-symbols-outlined">key</span>
                            {coupon.star_cost} Yıldız ile Aç
                        </button>
                    </div>
                )}

                {/* Unlocked Content */}
                {isPurchased && (
                    <div className="space-y-6">
                        {coupon.legs?.map((leg, index) => {
                            const legResult = leg.leg_result;
                            const isWon = legResult === 'won';
                            const isLost = legResult === 'lost';
                            const isPending = !legResult || legResult === 'pending';

                            const borderClass = isWon ? 'border-green-500/50' : isLost ? 'border-red-500/30' : 'border-white/5';
                            const bgClass = isWon ? 'bg-green-500/5' : isLost ? 'bg-red-500/5' : '';

                            return (
                                <div key={index} className={`bg-card-dark border ${borderClass} rounded-2xl overflow-hidden shadow-lg ${bgClass}`}>
                                    {/* Leg Header */}
                                    <div className="bg-white/5 px-5 py-3 border-b border-white/5 flex items-center justify-between">
                                        <div className="flex items-center gap-3">
                                            <div className={`size-8 rounded-lg flex items-center justify-center font-bold text-lg shadow-lg 
                                            ${isWon ? 'bg-green-500 text-white shadow-green-500/20' : isLost ? 'bg-red-500/50 text-red-200 shadow-red-500/10' : 'bg-primary text-white shadow-primary/20'}`}>
                                                {leg.leg_no}
                                            </div>
                                            <div className="flex flex-col leading-none">
                                                <span className="text-white font-bold text-base">. Koşu</span>
                                                <span className="text-xs text-gray-500 font-medium mt-0.5">{leg.race_time}</span>
                                            </div>
                                        </div>
                                        <div className="text-right flex items-center gap-3">
                                            {/* Result Badge */}
                                            {!isPending && (
                                                <div className={`flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-bold uppercase tracking-wide
                                                ${isWon ? 'bg-green-500/20 text-green-400 border border-green-500/30' : 'bg-red-500/20 text-red-400 border border-red-500/30'}`}>
                                                    <span className="material-symbols-outlined text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>
                                                        {isWon ? 'check_circle' : 'cancel'}
                                                    </span>
                                                    {isWon ? 'TUTTU' : 'TUTMADI'}
                                                </div>
                                            )}
                                            <div>
                                                <div className="text-xs font-bold text-gray-300 uppercase tracking-tight">{leg.race_info || 'Şartlı'}</div>
                                                <div className="text-[10px] text-gray-500 font-medium">{leg.distance || `${leg.field_size} Atlı`}</div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Actual Winner (if available) */}
                                    {leg.actual_winner && (
                                        <div className={`px-5 py-2 border-b border-white/5 flex items-center gap-2 text-xs
                                        ${isWon ? 'bg-green-500/10' : 'bg-red-500/10'}`}>
                                            <span className="material-symbols-outlined text-sm text-gray-400">emoji_events</span>
                                            <span className="text-gray-400">Kazanan:</span>
                                            <span className={`font-bold ${isWon ? 'text-green-400' : 'text-red-400'}`}>{leg.actual_winner}</span>
                                        </div>
                                    )}

                                    {/* Horses List */}
                                    <div className="divide-y divide-white/5">
                                        {leg.horses.map((horse, hIndex) => {
                                            const score = horse.ai_score || 75;
                                            const scoreColor = score >= 90 ? 'text-green-400' : score >= 80 ? 'text-accent-gold' : 'text-blue-400';
                                            const borderColor = score >= 90 ? 'border-green-400/30' : 'border-white/10';

                                            return (
                                                <div key={hIndex} className={`p-4 relative group ${horse.is_banko ? 'bg-gradient-to-r from-primary/5 to-transparent' : ''}`}>
                                                    {/* Banko Badge */}
                                                    {horse.is_banko && (
                                                        <div className="absolute top-0 right-0 p-2">
                                                            <span className="bg-primary/20 text-primary border border-primary/30 text-[10px] font-bold px-2 py-0.5 rounded shadow-[0_0_10px_rgba(255,215,0,0.1)] flex items-center gap-1">
                                                                <span className="material-symbols-outlined text-[12px]" style={{ fontVariationSettings: "'FILL' 1" }}>verified</span>
                                                                BANKO
                                                            </span>
                                                        </div>
                                                    )}

                                                    <div className="flex items-start gap-4">
                                                        {/* Left: Score Badge */}
                                                        <div className="flex flex-col items-center gap-1 pt-1">
                                                            <div className={`size-12 rounded-full border-2 ${borderColor} flex items-center justify-center bg-black/20 shadow-inner relative`}>
                                                                <span className={`text-sm font-black tracking-tighter ${scoreColor}`}>{score}</span>
                                                                <span className="absolute -bottom-1 text-[8px] uppercase font-bold text-gray-500 bg-black/50 px-1 rounded">Puan</span>
                                                            </div>

                                                            {/* Program No (Only if > 0) */}
                                                            {horse.program_no > 0 && (
                                                                <span className="text-[10px] items-center flex justify-center bg-white/5 w-6 h-4 rounded text-gray-500 font-mono">
                                                                    {horse.program_no}
                                                                </span>
                                                            )}
                                                        </div>

                                                        {/* Info */}
                                                        <div className="flex-1">
                                                            <div className="flex flex-col mb-2">
                                                                <h4 className={`text-lg font-bold leading-tight tracking-tight ${horse.is_banko ? 'text-white' : 'text-gray-200'}`}>
                                                                    {horse.horse_name}
                                                                </h4>
                                                                <div className="flex items-center gap-2 mt-1">
                                                                    <span className="text-xs text-gray-400 font-medium flex items-center gap-1 bg-white/5 px-2 py-0.5 rounded-full">
                                                                        <span className="material-symbols-outlined text-[14px]">person</span>
                                                                        {horse.jockey_name || '-'}
                                                                    </span>
                                                                </div>
                                                            </div>

                                                            {/* AI Note */}
                                                            {horse.ai_note && (
                                                                <div className="relative mt-3">
                                                                    <div className="absolute top-2 left-0 w-0.5 h-full max-h-[80%] bg-white/10 rounded-full"></div>
                                                                    <p className="text-xs text-gray-400 pl-3 leading-relaxed font-medium">
                                                                        {horse.ai_note}
                                                                    </p>
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>
                                            )
                                        })}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </main>

            {/* Modal Logic (Using same simple modal for verifying) */}
            {showUnlockModal && (
                <div className="fixed inset-0 z-[60] bg-black/80 backdrop-blur-sm flex items-end justify-center">
                    <div className="w-full max-w-md bg-zinc-900 rounded-t-3xl border-t border-white/10 p-6 pb-12 animate-in slide-in-from-bottom duration-300">
                        <div className="flex flex-col items-center text-center">
                            <h3 className="text-white text-xl font-bold mb-2">Kuponu Aç</h3>
                            <p className="text-gray-400 text-sm mb-6">Bakiyenizden <span className="text-primary font-bold">{coupon.star_cost} Yıldız</span> düşülecek.</p>
                            <div className="flex gap-3 w-full">
                                <button onClick={() => setShowUnlockModal(false)} className="flex-1 bg-white/10 text-white py-3 rounded-xl font-bold">İptal</button>
                                <button onClick={handleUnlock} className="flex-1 bg-primary text-white py-3 rounded-xl font-bold shadow-lg shadow-primary/20">Onayla</button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
