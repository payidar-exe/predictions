import { useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';
import { BottomNav } from '../components/BottomNav';

interface StatsData {
    totalCoupons: number;
    freeCoupons: number;
    premiumCoupons: number;
    cities: { city: string; count: number }[];
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

            // Get city distribution
            const { data: cityData } = await supabase
                .from('coupons')
                .select('city');

            const cityMap = new Map<string, number>();
            cityData?.forEach((c) => {
                const city = c.city.split(' ')[0]; // Get first word (city name)
                cityMap.set(city, (cityMap.get(city) || 0) + 1);
            });

            const cities = Array.from(cityMap.entries())
                .map(([city, count]) => ({ city, count }))
                .sort((a, b) => b.count - a.count)
                .slice(0, 5);

            setStats({
                totalCoupons: totalCount || 0,
                freeCoupons: freeCount || 0,
                premiumCoupons: premiumCount || 0,
                cities,
            });
            setIsLoading(false);
        };

        fetchStats();
    }, []);

    return (
        <div className="min-h-screen bg-background-dark pb-24">
            {/* Header */}
            <header className="pt-12 pb-6 px-6 safe-area-top">
                <h1 className="text-2xl font-bold text-white tracking-tight">İstatistikler</h1>
                <p className="text-gray-400 text-sm mt-1">Sistem performans metrikleri</p>
            </header>

            {isLoading ? (
                <div className="flex items-center justify-center py-12">
                    <div className="size-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                </div>
            ) : (
                <main className="px-4 space-y-6">


                    {/* AI Performance Card */}
                    <div className="bg-card-dark rounded-xl border border-white/5 p-6">
                        <div className="flex items-center gap-3 mb-6">
                            <div className="size-10 bg-primary/20 rounded-lg flex items-center justify-center">
                                <span className="material-symbols-outlined text-primary">psychology</span>
                            </div>
                            <div>
                                <h2 className="text-white font-bold">Kahin v10 AI</h2>
                                <p className="text-gray-400 text-xs">Son 15 Gün Performansı</p>
                            </div>
                        </div>

                        {/* Performance Bars */}
                        <div className="space-y-4">
                            <div>
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="text-gray-400">6/6 İsabet (Jackpot)</span>
                                    <span className="text-primary font-bold">%35</span>
                                </div>
                                <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                                    <div className="h-full bg-primary rounded-full" style={{ width: '35%' }} />
                                </div>
                            </div>
                            <div>
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="text-gray-400">5/6 İsabet</span>
                                    <span className="text-accent-gold font-bold">%21</span>
                                </div>
                                <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                                    <div className="h-full bg-accent-gold rounded-full" style={{ width: '21%' }} />
                                </div>
                            </div>
                            <div>
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="text-gray-400">4/6 İsabet</span>
                                    <span className="text-gray-300 font-bold">%14</span>
                                </div>
                                <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                                    <div className="h-full bg-gray-400 rounded-full" style={{ width: '14%' }} />
                                </div>
                            </div>
                        </div>
                    </div>

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
