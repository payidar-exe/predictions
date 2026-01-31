import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { supabase } from '../lib/supabase';
import { useAuthStore } from '../stores';
import { BottomNav } from '../components/BottomNav';

interface StarTransaction {
    id: string;
    amount: number;
    type: 'purchase' | 'spend' | 'bonus';
    description: string;
    created_at: string;
}

export function WalletPage() {
    const user = useAuthStore((s) => s.user);
    const [transactions, setTransactions] = useState<StarTransaction[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchTransactions = async () => {
            if (!user) return;

            const { data } = await supabase
                .from('star_transactions')
                .select('*')
                .eq('user_id', user.id)
                .order('created_at', { ascending: false })
                .limit(20);

            setTransactions(data || []);
            setIsLoading(false);
        };

        fetchTransactions();
    }, [user]);

    const getTransactionIcon = (type: string) => {
        switch (type) {
            case 'purchase': return { icon: 'add_circle', color: 'text-primary' };
            case 'spend': return { icon: 'remove_circle', color: 'text-red-400' };
            case 'bonus': return { icon: 'card_giftcard', color: 'text-accent-gold' };
            default: return { icon: 'circle', color: 'text-gray-400' };
        }
    };

    return (
        <div className="min-h-screen bg-background-dark pb-24">
            {/* Header */}
            <header className="pt-12 pb-6 px-6 safe-area-top">
                <h1 className="text-2xl font-bold text-white tracking-tight">Cüzdanım</h1>
                <p className="text-gray-400 text-sm mt-1">Yıldız bakiyenizi yönetin</p>
            </header>

            <main className="px-4 space-y-6">
                {/* Balance Card */}
                <div className="bg-gradient-to-br from-primary/30 to-accent-gold/20 rounded-2xl border border-white/10 p-6">
                    <p className="text-gray-300 text-sm mb-2">Mevcut Bakiye</p>
                    <div className="flex items-center gap-3 mb-6">
                        <span className="material-symbols-outlined text-accent-gold text-4xl" style={{ fontVariationSettings: "'FILL' 1" }}>
                            stars
                        </span>
                        <p className="text-5xl font-bold text-white">{user?.star_balance ?? 0}</p>
                        <span className="text-gray-400 text-xl">Yıldız</span>
                    </div>
                    <Link
                        to="/stars"
                        className="w-full bg-accent-gold hover:bg-accent-gold/90 text-background-dark py-3 rounded-xl font-bold flex items-center justify-center gap-2 transition-colors"
                    >
                        <span className="material-symbols-outlined">add</span>
                        <span>Yıldız Satın Al</span>
                    </Link>
                </div>

                {/* Quick Actions */}
                <div className="grid grid-cols-2 gap-3">
                    <Link
                        to="/my-coupons"
                        className="bg-card-dark rounded-xl border border-white/5 p-4 flex flex-col items-center gap-2 hover:bg-white/5 transition-colors"
                    >
                        <span className="material-symbols-outlined text-primary text-2xl">receipt_long</span>
                        <span className="text-white text-sm font-medium">Kuponlarım</span>
                    </Link>
                    <Link
                        to="/stars"
                        className="bg-card-dark rounded-xl border border-white/5 p-4 flex flex-col items-center gap-2 hover:bg-white/5 transition-colors"
                    >
                        <span className="material-symbols-outlined text-accent-gold text-2xl">shopping_cart</span>
                        <span className="text-white text-sm font-medium">Mağaza</span>
                    </Link>
                </div>

                {/* Transaction History */}
                <div className="bg-card-dark rounded-2xl border border-white/5 overflow-hidden">
                    <div className="px-6 py-4 border-b border-white/5">
                        <h2 className="text-white font-bold">İşlem Geçmişi</h2>
                    </div>

                    {isLoading ? (
                        <div className="flex items-center justify-center py-8">
                            <div className="size-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                        </div>
                    ) : transactions.length > 0 ? (
                        <div className="divide-y divide-white/5">
                            {transactions.map((tx) => {
                                const { icon, color } = getTransactionIcon(tx.type);
                                return (
                                    <div key={tx.id} className="px-6 py-4 flex items-center gap-4">
                                        <span className={`material-symbols-outlined ${color}`}>{icon}</span>
                                        <div className="flex-1">
                                            <p className="text-white text-sm font-medium">{tx.description}</p>
                                            <p className="text-gray-500 text-xs">
                                                {new Date(tx.created_at).toLocaleDateString('tr-TR', {
                                                    day: 'numeric',
                                                    month: 'short',
                                                    year: 'numeric',
                                                    hour: '2-digit',
                                                    minute: '2-digit',
                                                })}
                                            </p>
                                        </div>
                                        <p className={`font-bold ${tx.amount > 0 ? 'text-primary' : 'text-red-400'}`}>
                                            {tx.amount > 0 ? '+' : ''}{tx.amount}
                                        </p>
                                    </div>
                                );
                            })}
                        </div>
                    ) : (
                        <div className="py-8 text-center">
                            <span className="material-symbols-outlined text-4xl text-gray-600 mb-2">history</span>
                            <p className="text-gray-500 text-sm">Henüz işlem yok</p>
                        </div>
                    )}
                </div>
            </main>

            <BottomNav />
        </div>
    );
}
