import { Link } from 'react-router-dom';
import { useAuthStore } from '../stores';

const packages = [
    { id: 'pkg_100', name: '100 Yıldız', stars: 100, price: 49, isPopular: false },
    { id: 'pkg_250', name: '250 Yıldız', stars: 250, price: 99, isPopular: true },
    { id: 'pkg_500', name: '500 Yıldız', stars: 500, price: 179, isPopular: false },
];

export function BuyStarsPage() {
    const user = useAuthStore((s) => s.user);

    const handlePurchase = async (packageId: string) => {
        // TODO: Implement RevenueCat purchase flow
        console.log('Purchase:', packageId);
    };

    return (
        <div className="min-h-screen bg-background-dark">
            {/* Top Navigation */}
            <header className="sticky top-0 z-50 bg-background-dark/80 ios-blur border-b border-gray-800 safe-area-top">
                <div className="flex items-center p-4 justify-between max-w-md mx-auto">
                    <div className="flex items-center gap-2">
                        <Link to="/" className="text-gray-300">
                            <span className="material-symbols-outlined">arrow_back_ios</span>
                        </Link>
                        <h2 className="text-lg font-bold tracking-tight">Yıldız Mağazası</h2>
                    </div>
                    <div className="flex items-center gap-1.5 bg-gray-800 px-3 py-1 rounded-full border border-gray-700">
                        <span
                            className="material-symbols-outlined text-accent-gold text-sm"
                            style={{ fontVariationSettings: "'FILL' 1" }}
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
                    {packages.map((pkg) => (
                        <div key={pkg.id} className="relative group">
                            {pkg.isPopular && (
                                <div className="absolute -top-3 right-6 z-10 bg-gradient-to-r from-accent-gold to-yellow-400 text-black text-[10px] font-bold px-3 py-1 rounded-full uppercase tracking-widest shadow-lg">
                                    En Popüler
                                </div>
                            )}
                            <div
                                className={`flex items-center justify-between gap-4 rounded-xl bg-card-dark p-5 transition-all ${pkg.isPopular
                                        ? 'border-2 border-accent-gold shadow-[0_0_20px_rgba(194,157,70,0.15)]'
                                        : 'border border-gray-800 hover:border-primary/50'
                                    }`}
                            >
                                <div className="flex flex-col gap-4 flex-1">
                                    <div className="flex flex-col gap-1">
                                        <div className="flex items-center gap-2">
                                            <div className="flex -space-x-1">
                                                {Array.from({ length: Math.min(pkg.stars / 100, 3) }).map((_, i) => (
                                                    <span
                                                        key={i}
                                                        className="material-symbols-outlined text-accent-gold"
                                                        style={{ fontVariationSettings: "'FILL' 1" }}
                                                    >
                                                        stars
                                                    </span>
                                                ))}
                                            </div>
                                            <p className="text-xl font-bold">{pkg.name}</p>
                                        </div>
                                        <p
                                            className={`text-sm font-medium ${pkg.isPopular ? 'text-accent-gold/80' : 'text-gray-400'
                                                }`}
                                        >
                                            {pkg.isPopular ? 'Avantajlı Paket' : 'Standart Paket'}
                                        </p>
                                    </div>
                                    <div className="flex items-center justify-between mt-2">
                                        <span className="text-2xl font-bold text-primary">{pkg.price} TL</span>
                                        <button
                                            onClick={() => handlePurchase(pkg.id)}
                                            className="flex items-center justify-center rounded-lg h-10 px-6 bg-primary text-white text-sm font-bold transition-transform active:scale-95 shadow-lg shadow-primary/20"
                                        >
                                            Hemen Al
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Trust Section */}
                <div className="mt-12 px-4 text-center">
                    <div className="flex flex-col items-center gap-4 py-6 rounded-2xl bg-gray-800/30 border border-gray-800/50">
                        <div className="flex items-center gap-2 text-gray-400">
                            <span className="material-symbols-outlined text-sm">lock</span>
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
