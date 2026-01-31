import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { supabase } from '../lib/supabase';
import type { Coupon } from '../lib/supabase';
import { useAuthStore } from '../stores';
import { BottomNav } from '../components/BottomNav';

export function MyCouponsPage() {
    const user = useAuthStore((s) => s.user);
    const [coupons, setCoupons] = useState<Coupon[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchCoupons = async () => {
            if (!user) return;

            const { data } = await supabase
                .from('user_coupons')
                .select('coupon_id, coupons(*)')
                .eq('user_id', user.id)
                .order('purchased_at', { ascending: false });

            // Extract coupons from the joined data
            const purchasedCoupons = data
                ?.map((item) => (item.coupons as unknown) as Coupon)
                .filter((c): c is Coupon => c !== null && c !== undefined) ?? [];
            setCoupons(purchasedCoupons);
            setIsLoading(false);
        };

        fetchCoupons();
    }, [user]);

    return (
        <div className="min-h-screen bg-background-dark pb-24">
            {/* Header */}
            <header className="sticky top-0 z-40 bg-background-dark/80 ios-blur border-b border-white/5 safe-area-top">
                <div className="flex items-center gap-4 px-4 py-3">
                    <Link to="/profile" className="size-10 rounded-full hover:bg-white/10 flex items-center justify-center transition-colors">
                        <span className="material-symbols-outlined text-white">arrow_back</span>
                    </Link>
                    <h1 className="text-lg font-bold text-white">Satın Aldığım Kuponlar</h1>
                </div>
            </header>

            <main className="px-4 pt-6">
                {isLoading ? (
                    <div className="flex items-center justify-center py-12">
                        <div className="size-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                    </div>
                ) : coupons.length > 0 ? (
                    <div className="space-y-4">
                        {coupons.map((coupon) => (
                            <Link
                                key={coupon.id}
                                to={`/coupon/${coupon.id}`}
                                className="block bg-card-dark rounded-xl border border-white/5 p-4 hover:bg-white/5 transition-colors"
                            >
                                <div className="flex items-start justify-between">
                                    <div>
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className="material-symbols-outlined text-primary text-sm">location_on</span>
                                            <span className="text-gray-400 text-xs uppercase tracking-wider">{coupon.city}</span>
                                        </div>
                                        <h3 className="text-white font-bold">{coupon.title}</h3>
                                        <p className="text-gray-500 text-sm mt-1">{coupon.date}</p>
                                    </div>
                                    <span className="material-symbols-outlined text-primary">chevron_right</span>
                                </div>
                            </Link>
                        ))}
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center py-16 text-center">
                        <span className="material-symbols-outlined text-6xl text-gray-600 mb-4">receipt_long</span>
                        <h3 className="text-lg font-bold text-white mb-2">Henüz Kupon Yok</h3>
                        <p className="text-gray-500 text-sm mb-6">Premium kuponları satın aldığınızda burada görünecek.</p>
                        <Link
                            to="/"
                            className="bg-primary hover:bg-primary/90 text-white px-6 py-3 rounded-xl font-bold transition-colors"
                        >
                            Kuponları Keşfet
                        </Link>
                    </div>
                )}
            </main>

            <BottomNav />
        </div>
    );
}
