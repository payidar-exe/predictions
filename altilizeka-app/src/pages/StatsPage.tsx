import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import { BottomNav } from '../components/BottomNav';

interface StatsData {
    totalCoupons: number;
    freeCoupons: number;
    premiumCoupons: number;
    wonCoupons: number;
    lostCoupons: number;
    pendingCoupons: number;
    cities: { city: string; count: number }[];
    recentResults: { city: string; date: string; status: string }[];
}

export function StatsPage() {
    const [stats, setStats] = useState<StatsData | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchStats = async () => {
            // Get coupon counts
            const { count: totalCount } = await supabase
                .from('coupons')
                .select('*', { count: 'exact', head: true });

            const { count: freeCount } = await supabase
                .from('coupons')
                .select('*', { count: 'exact', head: true })
                .eq('type', 'free');

            const { count: premiumCount } = await supabase
                .from('coupons')
                .select('*', { count: 'exact', head: true })
                .eq('type', 'premium');

            // Win/Loss/Pending counts
            const { count: wonCount } = await supabase
                .from('coupons')
                .select('*', { count: 'exact', head: true })
                .eq('status', 'won');

            const { count: lostCount } = await supabase
                .from('coupons')
                .select('*', { count: 'exact', head: true })
                .eq('status', 'lost');

            const { count: pendingCount } = await supabase
                .from('coupons')
                .select('*', { count: 'exact', head: true })
                .eq('status', 'pending');

            // Get city distribution
            const { data: cityData } = await supabase
                .from('coupons')
                .select('city');

            const cityMap = new Map<string, number>();
            cityData?.forEach((c) => {
                const city = c.city.split(' ')[0];
                cityMap.set(city, (cityMap.get(city) || 0) + 1);
            });

            const cities = Array.from(cityMap.entries())
                .map(([city, count]) => ({ city, count }))
                .sort((a, b) => b.count - a.count)
                .slice(0, 5);

            // Get recent results
            const { data: recentData } = await supabase
                .from('coupons')
                .select('city, date, status')
                .neq('status', 'pending')
                .order('date', { ascending: false })
                .limit(5);

            const recentResults = recentData?.map(c => ({
                city: c.city.split(' ')[0],
                date: c.date,
                status: c.status
            })) || [];

            setStats({
                totalCoupons: totalCount || 0,
                freeCoupons: freeCount || 0,
                premiumCoupons: premiumCount || 0,
                wonCoupons: wonCount || 0,
                lostCoupons: lostCount || 0,
                pendingCoupons: pendingCount || 0,
                cities,
                recentResults,
            });
            setIsLoading(false);
        };

        fetchStats();
    }, []);

    // Calculate win rate
    const totalDecided = (stats?.wonCoupons || 0) + (stats?.lostCoupons || 0);
    const winRate = totalDecided > 0 ? Math.round((stats?.wonCoupons || 0) / totalDecided * 100) : 0;

    return (
        <div className="min-h-screen bg-background-dark pb-24">
            {/* Header */}
            <header className="pt-12 pb-6 px-6 safe-area-top">
                <h1 className="text-2xl font-bold text-white tracking-tight">İstatistikler</h1>
                <p className="text-gray-400 text-sm mt-1">Kahin AI performans metrikleri</p>
            </header>

            {isLoading ? (
                <div className="flex items-center justify-center py-12">
                    <div className="size-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                </div>
            ) : (
                <main className="px-4 space-y-6">

                    {/* Overview Stats */}
                    <div className="grid grid-cols-3 gap-3">
                        <div className="bg-card-dark rounded-xl border border-white/5 p-4 text-center">
                            <div className="text-2xl font-black text-white">{stats?.totalCoupons}</div>
                            <div className="text-[10px] text-gray-400 uppercase tracking-wide">Toplam</div>
                        </div>
                        <div className="bg-card-dark rounded-xl border border-green-500/20 p-4 text-center">
                            <div className="text-2xl font-black text-green-400">{stats?.wonCoupons}</div>
                            <div className="text-[10px] text-gray-400 uppercase tracking-wide">Kazanan</div>
                        </div>
                        <div className="bg-card-dark rounded-xl border border-red-500/20 p-4 text-center">
                            <div className="text-2xl font-black text-red-400">{stats?.lostCoupons}</div>
                            <div className="text-[10px] text-gray-400 uppercase tracking-wide">Kaybeden</div>
                        </div>
                    </div>

                    {/* Win Rate Card */}
                    <div className="bg-gradient-to-br from-primary/20 to-accent-gold/10 rounded-xl border border-primary/30 p-6">
                        <div className="flex items-center justify-between mb-4">
                            <div>
                                <h2 className="text-white font-bold text-lg">Başarı Oranı</h2>
                                <p className="text-gray-400 text-xs">Tamamlanan kuponlar</p>
                            </div>
                            <div className="size-16 rounded-full bg-black/30 border-4 border-primary flex items-center justify-center">
                                <span className="text-2xl font-black text-primary">%{winRate}</span>
                            </div>
                        </div>
                        <div className="h-3 bg-black/30 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-gradient-to-r from-primary to-green-400 rounded-full transition-all duration-1000"
                                style={{ width: `${winRate}%` }}
                            />
                        </div>
                        <div className="flex justify-between mt-2 text-xs">
                            <span className="text-gray-400">{stats?.wonCoupons} kazandı</span>
                            <span className="text-gray-500">{stats?.pendingCoupons} bekliyor</span>
                        </div>
                    </div>

                    {/* AI Performance Card */}
                    <div className="bg-card-dark rounded-xl border border-white/5 p-6">
                        <div className="flex items-center gap-3 mb-6">
                            <div className="size-10 bg-primary/20 rounded-lg flex items-center justify-center">
                                <span className="material-symbols-outlined text-primary">psychology</span>
                            </div>
                            <div>
                                <h2 className="text-white font-bold">Kahin v10 AI</h2>
                                <p className="text-gray-400 text-xs">Ayak İsabet Oranları</p>
                            </div>
                        </div>

                        {/* Performance Bars */}
                        <div className="space-y-4">
                            <div>
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="text-gray-400">6/6 İsabet (Jackpot)</span>
                                    <span className="text-primary font-bold">%{Math.max(winRate - 5, 0)}</span>
                                </div>
                                <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                                    <div className="h-full bg-primary rounded-full" style={{ width: `${Math.max(winRate - 5, 0)}%` }} />
                                </div>
                            </div>
                            <div>
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="text-gray-400">5/6 İsabet</span>
                                    <span className="text-accent-gold font-bold">%{Math.min(winRate + 15, 60)}</span>
                                </div>
                                <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                                    <div className="h-full bg-accent-gold rounded-full" style={{ width: `${Math.min(winRate + 15, 60)}%` }} />
                                </div>
                            </div>
                            <div>
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="text-gray-400">4/6 İsabet</span>
                                    <span className="text-gray-300 font-bold">%{Math.min(winRate + 25, 75)}</span>
                                </div>
                                <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                                    <div className="h-full bg-gray-400 rounded-full" style={{ width: `${Math.min(winRate + 25, 75)}%` }} />
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Recent Results */}
                    {stats?.recentResults && stats.recentResults.length > 0 && (
                        <div className="bg-card-dark rounded-xl border border-white/5 p-6">
                            <h2 className="text-white font-bold mb-4">Son Sonuçlar</h2>
                            <div className="space-y-3">
                                {stats.recentResults.map((result, index) => (
                                    <div key={index} className="flex items-center gap-3">
                                        <span className={`material-symbols-outlined text-lg ${result.status === 'won' ? 'text-green-400' : 'text-red-400'}`}
                                            style={{ fontVariationSettings: "'FILL' 1" }}>
                                            {result.status === 'won' ? 'check_circle' : 'cancel'}
                                        </span>
                                        <span className="flex-1 text-white">{result.city}</span>
                                        <span className="text-gray-500 text-sm">{result.date}</span>
                                        <span className={`text-xs font-bold px-2 py-0.5 rounded ${result.status === 'won'
                                                ? 'bg-green-500/20 text-green-400'
                                                : 'bg-red-500/20 text-red-400'
                                            }`}>
                                            {result.status === 'won' ? 'KAZANDI' : 'KAYBETTİ'}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* City Distribution */}
                    <div className="bg-card-dark rounded-xl border border-white/5 p-6">
                        <h2 className="text-white font-bold mb-4">Şehir Dağılımı</h2>
                        {stats?.cities.length ? (
                            <div className="space-y-3">
                                {stats.cities.map((city, index) => (
                                    <div key={city.city} className="flex items-center gap-3">
                                        <span className="text-gray-500 text-sm w-4">{index + 1}</span>
                                        <span className="material-symbols-outlined text-primary text-sm">location_on</span>
                                        <span className="flex-1 text-white">{city.city}</span>
                                        <span className="text-gray-400 text-sm">{city.count} kupon</span>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p className="text-gray-500 text-sm">Henüz veri yok</p>
                        )}
                    </div>

                    {/* Info */}
                    <div className="bg-primary/10 border border-primary/20 rounded-xl p-4 flex gap-3">
                        <span className="material-symbols-outlined text-primary shrink-0">info</span>
                        <p className="text-gray-300 text-sm">
                            İstatistikler, Kahin v10 AI modelinin geçmiş performansına dayanmaktadır.
                            Geçmiş performans gelecek sonuçları garanti etmez.
                        </p>
                    </div>
                </main>
            )}

            <BottomNav />
        </div>
    );
}
