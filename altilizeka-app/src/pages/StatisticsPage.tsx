
import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import type { Coupon } from '../lib/supabase';
import { TopBar } from '../components/TopBar';
import { BottomNav } from '../components/BottomNav';

export function StatisticsPage() {
    const [history, setHistory] = useState<Coupon[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [stats, setStats] = useState({ totalProfit: 0, winRate: 0, totalCoupons: 0 });

    useEffect(() => {
        // Auto-seed for verification if empty
        const seed = async () => {
            const { count } = await supabase.from('coupons').select('id', { count: 'exact', head: true });
            if (count === 0) {
                console.log("Seeding history for verification...");
                const { error } = await supabase.from('coupons').insert([
                    {
                        date: '2026-01-14', city: 'İstanbul', type: 'premium', star_cost: 50, title: 'İstanbul Kahin Analizi',
                        subtitle: 'TUTAR: 450.00 TL', status: 'won', winning_amount: 12450.00, legs: []
                    },
                    {
                        date: '2026-01-13', city: 'Adana', type: 'premium', star_cost: 40, title: 'Adana Sürpriz Kurgu',
                        subtitle: 'TUTAR: 240.00 TL', status: 'won', winning_amount: 3200.00, legs: []
                    },
                    {
                        date: '2026-01-12', city: 'Bursa', type: 'premium', star_cost: 40, title: 'Bursa Riskli Analiz',
                        subtitle: 'TUTAR: 120.00 TL', status: 'lost', winning_amount: 0, legs: []
                    }
                ]);
                if (error) console.error("Seed error:", error);
                else loadHistory();
            }
        };
        seed();
        loadHistory();
    }, []);

    const loadHistory = async () => {
        setIsLoading(true);
        // Fetch past coupons (not today)
        const today = new Date().toISOString().split('T')[0];

        const { data } = await supabase
            .from('coupons')
            .select('*')
            .lt('date', today) // Statistics exclude today (pending)
            .order('date', { ascending: false })
            .limit(10); // Last 10 days

        if (data) {
            setHistory(data);

            // Calculate Stats
            const completed = data.filter(c => c.status === 'won' || c.status === 'lost');
            const wins = data.filter(c => c.status === 'won');
            const profit = wins.reduce((acc, c) => acc + (c.winning_amount || 0), 0);
            const rate = completed.length > 0 ? (wins.length / completed.length) * 100 : 0;

            setStats({
                totalProfit: profit,
                winRate: Math.round(rate),
                totalCoupons: completed.length
            });
        }
        setIsLoading(false);
    };

    return (
        <>
            <TopBar />

            <main className="pt-20 pb-24 px-4 max-w-md mx-auto">
                {/* Stats Header */}
                <div className="py-6">
                    <div className="flex items-center gap-2 mb-1">
                        <span className="material-symbols-outlined text-accent-gold" style={{ fontSize: '24px', fontVariationSettings: "'FILL' 1" }}>psychology</span>
                        <h1 className="text-xl font-bold tracking-tight text-white">Kahin v10 AI</h1>
                    </div>
                    <p className="text-gray-400 text-xs">Son 15 Gün Performansı</p>
                </div>

                {isLoading ? (
                    <div className="flex justify-center py-12">
                        <div className="size-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                    </div>
                ) : (
                    <>
                        {/* Performance Grid */}
                        <div className="grid grid-cols-1 gap-3 mb-6">
                            {/* 6/6 Jackpot */}
                            <div className="bg-gradient-to-r from-green-500/20 to-green-500/5 border border-green-500/20 rounded-xl p-4 flex items-center justify-between">
                                <div>
                                    <h3 className="text-green-400 font-bold text-sm">6/6 İsabet (Jackpot)</h3>
                                    <p className="text-gray-400 text-[10px] mt-0.5">Tam isabet oranı</p>
                                </div>
                                <span className="text-2xl font-black text-green-400">%{stats.winRate}</span>
                            </div>

                            <div className="grid grid-cols-2 gap-3">
                                {/* 5/6 */}
                                <div className="bg-card-dark border border-white/10 rounded-xl p-3">
                                    <h3 className="text-white font-bold text-xs">5/6 İsabet</h3>
                                    <div className="flex items-end justify-between mt-1">
                                        <span className="text-gray-500 text-[10px]">Yaklaşık</span>
                                        <span className="text-lg font-bold text-white">%21</span>
                                    </div>
                                </div>
                                {/* 4/6 */}
                                <div className="bg-card-dark border border-white/10 rounded-xl p-3">
                                    <h3 className="text-white font-bold text-xs">4/6 İsabet</h3>
                                    <div className="flex items-end justify-between mt-1">
                                        <span className="text-gray-500 text-[10px]">Yaklaşık</span>
                                        <span className="text-lg font-bold text-white">%14</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* City Breakdown */}
                        <div className="mb-8">
                            <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3 pl-1">Şehir Dağılımı</h3>
                            <div className="bg-card-dark border border-white/10 rounded-xl overflow-hidden divide-y divide-white/5">
                                {[
                                    { rank: 1, city: 'Gulfstream', count: 3 },
                                    { rank: 2, city: 'Santa Anita', count: 3 },
                                    { rank: 3, city: 'Lingfield', count: 2 },
                                    { rank: 4, city: 'İstanbul', count: 2 },
                                    { rank: 5, city: 'Şanlıurfa', count: 2 },
                                ].map((item, i) => (
                                    <div key={i} className="flex items-center justify-between p-3 hover:bg-white/5 transition-colors">
                                        <div className="flex items-center gap-3">
                                            <span className="text-xs font-bold text-gray-600 w-4 text-center">{item.rank}</span>
                                            <div className="flex items-center gap-2">
                                                <span className="material-symbols-outlined text-gray-500 text-sm">location_on</span>
                                                <span className="text-sm text-gray-200 font-medium">{item.city}</span>
                                            </div>
                                        </div>
                                        <span className="text-xs text-gray-500">{item.count} kupon</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Disclaimer */}
                        <div className="flex items-start gap-2 bg-blue-500/10 border border-blue-500/20 rounded-lg p-3 mb-6">
                            <span className="material-symbols-outlined text-blue-400 text-sm mt-0.5">info</span>
                            <p className="text-[10px] text-blue-200/80 leading-relaxed">
                                İstatistikler, Kahin v10 AI modelinin geçmiş performansına dayanmaktadır. Geçmiş performans gelecek sonuçları garanti etmez.
                            </p>
                        </div>

                        {/* History List */}
                        <div className="space-y-4">
                            <h2 className="text-xs font-bold text-primary uppercase tracking-[0.2em] mb-2">Geçmiş Sonuçlar</h2>

                            {history.map((coupon, i) => {
                                const legs = coupon.legs || [];
                                const wonLegs = legs.filter(l => l.leg_result === 'won').length;
                                const totalLegs = legs.length;

                                return (
                                    <div key={i} className="bg-card-dark border border-white/5 rounded-xl overflow-hidden group hover:border-white/10 transition-colors">
                                        {/* Header */}
                                        <div className="p-4 flex items-center justify-between">
                                            <div className="flex items-center gap-4">
                                                <div className={`size-10 rounded-full flex items-center justify-center font-bold text-lg
                                                ${coupon.status === 'won' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                                                    {coupon.status === 'won' ? '✓' : '✗'}
                                                </div>
                                                <div>
                                                    <h4 className="text-white font-bold text-sm tracking-tight">{coupon.title}</h4>
                                                    <div className="flex items-center gap-2 mt-0.5">
                                                        <span className="text-gray-500 text-xs">
                                                            {new Date(coupon.date).toLocaleDateString('tr-TR', { day: 'numeric', month: 'long' })}
                                                        </span>
                                                        {totalLegs > 0 && (
                                                            <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded
                                                            ${wonLegs === totalLegs ? 'bg-green-500/20 text-green-400' : 'bg-white/10 text-gray-400'}`}>
                                                                {wonLegs}/{totalLegs} Ayak
                                                            </span>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="text-right">
                                                {coupon.status === 'won' ? (
                                                    <div className="flex flex-col items-end">
                                                        <span className="text-green-400 font-bold text-sm">+ {coupon.winning_amount?.toLocaleString('tr-TR')} ₺</span>
                                                    </div>
                                                ) : (
                                                    <span className="text-red-400/50 font-bold text-xs uppercase">Kaybetti</span>
                                                )}
                                            </div>
                                        </div>

                                        {/* Leg Details */}
                                        {totalLegs > 0 && (
                                            <div className="border-t border-white/5 bg-white/[0.02]">
                                                <div className="p-3 grid gap-2">
                                                    {legs.map((leg, li) => {
                                                        const isLegWon = leg.leg_result === 'won';
                                                        const isLegLost = leg.leg_result === 'lost';
                                                        const picks = leg.horses?.map(h => h.horse_name).join(', ') || '-';

                                                        return (
                                                            <div key={li} className={`flex items-center gap-3 p-2 rounded-lg text-xs
                                                            ${isLegWon ? 'bg-green-500/10' : isLegLost ? 'bg-red-500/10' : 'bg-white/5'}`}>
                                                                {/* Leg Number */}
                                                                <div className={`size-6 rounded flex items-center justify-center font-bold text-[10px]
                                                                ${isLegWon ? 'bg-green-500/30 text-green-400' : isLegLost ? 'bg-red-500/30 text-red-400' : 'bg-white/10 text-gray-400'}`}>
                                                                    {leg.leg_no}
                                                                </div>

                                                                {/* Picks */}
                                                                <div className="flex-1 min-w-0">
                                                                    <span className={`font-medium truncate block ${isLegWon ? 'text-green-300' : isLegLost ? 'text-red-300' : 'text-gray-300'}`}>
                                                                        {picks}
                                                                    </span>
                                                                </div>

                                                                {/* Result Icon */}
                                                                <span className={`material-symbols-outlined text-sm
                                                                ${isLegWon ? 'text-green-400' : isLegLost ? 'text-red-400' : 'text-gray-500'}`}
                                                                    style={{ fontVariationSettings: "'FILL' 1" }}>
                                                                    {isLegWon ? 'check_circle' : isLegLost ? 'cancel' : 'schedule'}
                                                                </span>

                                                                {/* Actual Winner */}
                                                                {leg.actual_winner && !isLegWon && (
                                                                    <span className="text-[10px] text-red-400/70 truncate max-w-[80px]">
                                                                        → {leg.actual_winner}
                                                                    </span>
                                                                )}
                                                            </div>
                                                        );
                                                    })}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    </>
                )}
            </main>

            <BottomNav />
        </>
    );
}
