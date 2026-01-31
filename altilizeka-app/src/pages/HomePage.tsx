import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { TopBar } from '../components/TopBar';
import { BottomNav } from '../components/BottomNav';
import { PremiumCouponCard } from '../components/CouponCard';
import { AdWatchModal } from '../components/AdWatchModal';
import { useCouponStore, useAuthStore } from '../stores';

interface BankoPick {
    horseName: string;
    raceTime: string;
    city: string;
    aiNote: string | null;
}

export function HomePage() {
    const { coupons, isLoading, fetchTodayCoupons } = useCouponStore();
    const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
    const navigate = useNavigate();

    const [isAdOpen, setIsAdOpen] = useState(false);
    const [bankoPicks, setBankoPicks] = useState<BankoPick[]>([]);
    const [unlockedBankos, setUnlockedBankos] = useState<Set<string>>(new Set());

    useEffect(() => {
        fetchTodayCoupons();
    }, [fetchTodayCoupons]);

    // Load unlocked status on mount
    useEffect(() => {
        // Scan local storage or just wait for render?
        // Better: we can check for specific keys if we know them, but we don't know keys until bankoPicks are loaded.
        // So we do this in the bankoPicks effect or just check during render? 
        // Checking during render with state sync is cleaner.
    }, []);

    useEffect(() => {
        // Extract banko predictions from all coupons
        if (coupons.length > 0) {
            const picks: BankoPick[] = [];
            coupons.forEach(coupon => {
                coupon.legs?.forEach(leg => {
                    leg.horses.forEach(horse => {
                        if (horse.is_banko) {
                            picks.push({
                                horseName: horse.horse_name,
                                raceTime: leg.race_time,
                                city: coupon.city,
                                aiNote: horse.ai_note
                            });
                        }
                    });
                });
            });
            // Limit to 2 picks
            const finalPicks = picks.slice(0, 2);
            setBankoPicks(finalPicks);

            // Sync unlocked state for these picks
            const today = new Date().toISOString().split('T')[0];
            const newUnlocked = new Set<string>();
            finalPicks.forEach(pick => {
                const pickId = `${pick.city}-${pick.horseName}`.replace(/\s+/g, '-').toLowerCase();
                if (localStorage.getItem(`banko_${pickId}_${today}`) === 'true') {
                    newUnlocked.add(pickId);
                }
            });
            setUnlockedBankos(newUnlocked);
        }
    }, [coupons]);

    useEffect(() => {
        // Init global for passing ID (simple solution)
        if (typeof window !== 'undefined') {
            (window as any).pendingUnlockId = null;
        }
    }, []);

    const premiumCoupons = coupons.filter((c) => c.type === 'premium');

    const handleCouponClick = (e: React.MouseEvent, couponId: string) => {
        e.preventDefault();
        if (!isAuthenticated) {
            if (confirm('Tahminleri görmek için giriş yapmalısınız veya kayıt olmalısınız.')) {
                navigate('/login');
            }
            return;
        }
        navigate(`/coupon/${couponId}`);
    };

    const handleUnlockReward = () => {
        const today = new Date().toISOString().split('T')[0];
        const targetId = (window as any).pendingUnlockId;

        if (targetId) {
            localStorage.setItem(`banko_${targetId}_${today}`, 'true');
            // Update state
            setUnlockedBankos(prev => {
                const next = new Set(prev);
                next.add(targetId);
                return next;
            });
            (window as any).pendingUnlockId = null;
        }
    };

    return (
        <>
            <TopBar />
            <AdWatchModal
                isOpen={isAdOpen}
                onClose={() => setIsAdOpen(false)}
                onReward={handleUnlockReward}
            />

            <main className="pt-20 pb-24 px-4 max-w-md mx-auto">
                {/* Header */}
                <div className="py-6">
                    <h1 className="text-3xl font-bold tracking-tight text-white">Günün Tahminleri</h1>
                    <p className="text-gray-400 text-sm mt-1">Yapay zeka analizli at yarışı kuponları</p>
                </div>

                {/* Loading State */}
                {isLoading && (
                    <div className="flex items-center justify-center py-12">
                        <div className="size-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                    </div>
                )}

                {/* Rewarded Banko Section */}
                {bankoPicks.length > 0 && (
                    <section className="mb-8">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-xs font-bold text-primary uppercase tracking-[0.2em]">
                                Günün Banko Adayları
                            </h2>
                            <div className="h-[1px] flex-1 bg-primary/20 ml-4" />
                        </div>

                        <div className="grid gap-4">
                            {bankoPicks.map((pick, i) => {
                                const pickId = `${pick.city}-${pick.horseName}`.replace(/\s+/g, '-').toLowerCase();
                                const isUnlocked = unlockedBankos.has(pickId);

                                return (
                                    <div key={i} className="relative overflow-hidden rounded-2xl border border-primary/30 bg-card-dark">
                                        {/* Content Layer */}
                                        <div className={`p-4 transition-all duration-500 ${!isUnlocked ? 'blur-md opacity-40' : ''}`}>
                                            <div className="flex items-start gap-4">
                                                <div className="size-12 bg-primary/20 rounded-full flex items-center justify-center shrink-0">
                                                    <span className="text-primary font-bold text-lg">{i + 1}</span>
                                                </div>
                                                <div>
                                                    <div className="flex items-center gap-2 mb-1">
                                                        <span className="text-xs font-bold text-primary bg-primary/10 px-2 py-0.5 rounded uppercase">{pick.city}</span>
                                                        <span className="text-xs text-gray-400">{pick.raceTime}</span>
                                                    </div>
                                                    <h3 className="text-xl font-bold text-white mb-1">{pick.horseName}</h3>
                                                    <p className="text-sm text-gray-400 italic">"{pick.aiNote}"</p>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Lock Layer */}
                                        {!isUnlocked && (
                                            <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-black/40 backdrop-blur-[2px] p-4 text-center">
                                                <div className="size-10 bg-primary/20 rounded-full flex items-center justify-center mb-2 animate-pulse">
                                                    <span className="material-symbols-outlined text-2xl text-primary" style={{ fontVariationSettings: "'FILL' 1" }}>lock</span>
                                                </div>
                                                <button
                                                    onClick={() => {
                                                        if (!isAuthenticated) {
                                                            if (confirm('Banko tahminleri görmek için giriş yapmalısınız veya kayıt olmalısınız.')) {
                                                                navigate('/login');
                                                            }
                                                            return;
                                                        }
                                                        // Set pending unlock ID
                                                        (window as any).pendingUnlockId = pickId;
                                                        setIsAdOpen(true);
                                                    }}
                                                    className="bg-primary hover:bg-primary/90 text-white px-4 py-2 rounded-lg font-bold text-sm flex items-center gap-2 transition-all hover:scale-105 shadow-lg shadow-primary/25"
                                                >
                                                    <span className="material-symbols-outlined text-lg">play_circle</span>
                                                    <span>İzle & Aç</span>
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    </section>
                )}

                {/* Premium Coupons Section */}
                {premiumCoupons.length > 0 && (
                    <section className="space-y-6 mb-8">
                        <div className="flex items-center justify-between mb-4">
                            <h2 className="text-xs font-bold text-accent-gold uppercase tracking-[0.2em]">
                                Premium Analizler
                            </h2>
                            <div className="h-[1px] flex-1 bg-accent-gold/20 ml-4" />
                        </div>
                        {premiumCoupons.map((coupon) => {
                            const isUnlocked = useCouponStore.getState().purchasedCouponIds.includes(coupon.id);
                            return (
                                <div key={coupon.id} onClick={(e) => handleCouponClick(e, coupon.id)} className="cursor-pointer">
                                    <PremiumCouponCard coupon={coupon} isUnlocked={isUnlocked} />
                                </div>
                            );
                        })}
                    </section>
                )}

                {/* Empty State - Time Aware */}
                {!isLoading && coupons.length === 0 && (() => {
                    const now = new Date();
                    const hour = now.getHours();
                    const isBefore10 = hour < 10;

                    return (
                        <div className="flex flex-col items-center justify-center py-16 text-center">
                            <div className="size-20 bg-primary/10 rounded-full flex items-center justify-center mb-6">
                                <span className="material-symbols-outlined text-5xl text-primary">
                                    {isBefore10 ? 'schedule' : 'calendar_today'}
                                </span>
                            </div>

                            {isBefore10 ? (
                                <>
                                    <h3 className="text-xl font-bold text-white mb-2">Tahminler Hazırlanıyor</h3>
                                    <p className="text-gray-400 text-sm max-w-[250px]">
                                        Günün kuponları saat <span className="text-primary font-bold">10:00</span>'da yayınlanacak.
                                    </p>
                                    <div className="mt-6 bg-card-dark border border-white/10 rounded-xl px-6 py-4">
                                        <div className="flex items-center gap-3">
                                            <span className="material-symbols-outlined text-primary animate-pulse">hourglass_top</span>
                                            <span className="text-white font-mono text-lg">10:00'ı Bekleyin</span>
                                        </div>
                                    </div>
                                </>
                            ) : (
                                <>
                                    <h3 className="text-lg font-bold text-white mb-2">Bugün Kupon Yok</h3>
                                    <p className="text-gray-500 text-sm">Yarış günlerinde yeni tahminler yayınlanır.</p>
                                </>
                            )}
                        </div>
                    );
                })()}
            </main>

            <BottomNav />
        </>
    );
}
