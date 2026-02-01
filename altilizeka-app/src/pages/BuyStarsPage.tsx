import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuthStore } from '../stores';
import { getOfferings, purchasePackage } from '../lib/revenuecat';
import { Capacitor } from '@capacitor/core';
import type { PurchasesPackage } from '@revenuecat/purchases-capacitor';

const fallbackPackages = [
    { id: 'pkg_100', name: '100 Yıldız', stars: 100, price: '49 TL', isPopular: false, identifier: 'pkg_100' },
    { id: 'pkg_250', name: '250 Yıldız', stars: 250, price: '99 TL', isPopular: true, identifier: 'pkg_250' },
    { id: 'pkg_500', name: '500 Yıldız', stars: 500, price: '179 TL', isPopular: false, identifier: 'pkg_500' },
];

export function BuyStarsPage() {
    const user = useAuthStore((s) => s.user);
    const updateStarBalance = useAuthStore((s) => s.updateStarBalance);
    const [rcPackages, setRcPackages] = useState<PurchasesPackage[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        const fetchPackages = async () => {
            if (Capacitor.isNativePlatform()) {
                setIsLoading(true);
                try {
                    const currentOffering = await getOfferings();
                    if (currentOffering && currentOffering.availablePackages) {
                        setRcPackages(currentOffering.availablePackages);
                    }
                } catch (error) {
                    console.error('Error fetching packages:', error);
                }
                setIsLoading(false);
            }
        };
        fetchPackages();
    }, []);

    const handlePurchase = async (pkg: PurchasesPackage | typeof fallbackPackages[0]) => {
        if (Capacitor.isNativePlatform()) {
            setIsLoading(true);
            const success = await purchasePackage(pkg as PurchasesPackage);
            if (success) {
                // Determine stars from package identifier or metadata
                const identifier = 'identifier' in pkg ? pkg.identifier : pkg.id;
                const stars = parseInt(identifier.split('_')[1]) || 0;
                updateStarBalance(stars);
                alert('Satın alma başarılı! Yıldızlarınız hesabınıza eklendi.');
            }
            setIsLoading(false);
        } else {
            // Web Mock
            const identifier = 'identifier' in pkg ? pkg.identifier : pkg.id;
            console.log('Purchase (Web Mock):', identifier);
            alert('Bu işlem sadece mobil uygulamada geçerlidir.');
        }
    };

    return (
        <div className="min-h-screen bg-background-dark">
            {/* Top Navigation */}
            <header className="sticky top-0 z-50 bg-background-dark/80 backdrop-blur-md border-b border-gray-800 safe-area-top">
                <div className="flex items-center p-4 justify-between max-w-md mx-auto">
                    <div className="flex items-center gap-2">
                        <Link to="/" className="text-gray-300">
                            <span className="material-symbols-outlined font-icon">arrow_back_ios</span>
                        </Link>
                        <h2 className="text-lg font-bold tracking-tight">Yıldız Mağazası</h2>
                    </div>
                    <div className="flex items-center gap-1.5 bg-gray-800 px-3 py-1 rounded-full border border-gray-700">
                        <span
                            className="material-symbols-outlined text-accent-gold text-sm font-icon filled"
                        >
                            stars
                        </span>
                        <span className="text-sm font-bold">{user?.star_balance ?? 0}</span>
                    </div>
                </div>
            </header>

            <main className="max-w-md mx-auto pb-10">
                {/* Header */}
                <div className="px-4 pt-8 pb-4">
                    <h1 className="text-3xl font-bold tracking-tight text-white">Yıldız Paketi Seç</h1>
                    <p className="text-gray-400 mt-2 text-sm leading-relaxed">
                        Pro tahminlere ve özel kuponlara erişmek için yıldız bakiyenizi hemen güncelleyin.
                    </p>
                </div>

                {/* Package Cards */}
                <div className="flex flex-col gap-4 px-4 mt-4">
                    {isLoading ? (
                        <div className="flex flex-col items-center py-12">
                            <div className="size-10 border-2 border-primary border-t-transparent rounded-full animate-spin mb-4" />
                            <p className="text-gray-400 text-sm">Paketler yükleniyor...</p>
                        </div>
                    ) : (
                        (rcPackages.length > 0 ? rcPackages : fallbackPackages).map((pkg) => {
                            // Extract data from RC package or fallback
                            const pkgIdentifier = 'identifier' in pkg ? pkg.identifier : pkg.id;
                            const title = 'product' in pkg ? pkg.product.title : pkg.name;
                            const price = 'product' in pkg ? pkg.product.priceString : pkg.price;
                            const stars = 'identifier' in pkg ? parseInt(pkgIdentifier.split('_')[1]) || 0 : pkg.stars;
                            const isPopular = pkgIdentifier.includes('250') || (('isPopular' in pkg) && pkg.isPopular);

                            return (
                                <div key={pkgIdentifier} className="relative group">
                                    {isPopular && (
                                        <div className="absolute -top-3 right-6 z-10 bg-gradient-to-r from-accent-gold to-yellow-400 text-black text-[10px] font-bold px-3 py-1 rounded-full uppercase tracking-widest shadow-lg">
                                            En Popüler
                                        </div>
                                    )}
                                    <div
                                        className={`flex items-center justify-between gap-4 rounded-xl bg-card-dark p-5 transition-all ${isPopular
                                            ? 'border-2 border-accent-gold shadow-[0_0_20px_rgba(194,157,70,0.15)]'
                                            : 'border border-gray-800 hover:border-primary/50'
                                            }`}
                                    >
                                        <div className="flex flex-col gap-4 flex-1">
                                            <div className="flex flex-col gap-1">
                                                <div className="flex items-center gap-2">
                                                    <div className="flex -space-x-1">
                                                        {Array.from({ length: Math.min(stars / 100, 3) }).map((_, i) => (
                                                            <span
                                                                key={i}
                                                                className="material-symbols-outlined text-accent-gold font-icon filled"
                                                            >
                                                                stars
                                                            </span>
                                                        ))}
                                                    </div>
                                                    <p className="text-xl font-bold">{title}</p>
                                                </div>
                                                <p
                                                    className={`text-sm font-medium ${isPopular ? 'text-accent-gold/80' : 'text-gray-400'
                                                        }`}
                                                >
                                                    {isPopular ? 'Avantajlı Paket' : 'Standart Paket'}
                                                </p>
                                            </div>
                                            <div className="flex items-center justify-between mt-2">
                                                <span className="text-2xl font-bold text-primary">{price}</span>
                                                <button
                                                    onClick={() => handlePurchase(pkg)}
                                                    disabled={isLoading}
                                                    className="flex items-center justify-center rounded-lg h-10 px-6 bg-primary text-white text-sm font-bold transition-transform active:scale-95 shadow-lg shadow-primary/20 disabled:opacity-50"
                                                >
                                                    Hemen Al
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            );
                        })
                    )}
                </div>

                {/* Trust Section */}
                <div className="mt-12 px-4 text-center">
                    <div className="flex flex-col items-center gap-4 py-6 rounded-2xl bg-gray-800/30 border border-gray-800/50">
                        <div className="flex items-center gap-2 text-gray-400">
                            <span className="material-symbols-outlined text-sm font-icon">lock</span>
                            <p className="text-xs font-medium uppercase tracking-widest">256-bit SSL Güvenli Ödeme</p>
                        </div>
                        <p className="text-[10px] text-gray-600 px-6 leading-tight">
                            Ödemeleriniz App Store / Play Store üzerinden güvenli bir şekilde gerçekleştirilir.
                        </p>
                    </div>
                </div>
            </main>
        </div>
    );
}
