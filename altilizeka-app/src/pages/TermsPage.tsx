import { Link } from 'react-router-dom';

export function TermsPage() {
    return (
        <div className="min-h-screen bg-background-dark pb-12">
            {/* Header */}
            <header className="sticky top-0 z-40 bg-background-dark/95 ios-blur border-b border-white/5 safe-area-top">
                <div className="flex items-center gap-4 px-4 py-3">
                    <Link to="/login" className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors">
                        <span className="material-symbols-outlined">arrow_back</span>
                        <span className="text-sm font-medium">Geri</span>
                    </Link>
                    <h1 className="text-lg font-bold text-white text-center flex-1 pr-16">Kullanım Koşulları</h1>
                </div>
            </header>

            <main className="px-6 py-8 prose prose-invert prose-sm max-w-none">
                <h2 className="text-white font-bold text-lg mb-4">1. Kabul Edilme</h2>
                <p className="text-gray-400 mb-6">
                    AltılıZeka uygulamasını indirerek ve kullanarak bu koşulları kabul etmiş olursunuz.
                </p>

                <h2 className="text-white font-bold text-lg mb-4">2. Hizmetin Niteliği</h2>
                <p className="text-gray-400 mb-6">
                    AltılıZeka, yapay zeka destekli istatistiksel tahminler sunar. Bu tahminler bilgilendirme amaçlıdır ve kesin kazanç garantisi vermez. At yarışı bir şans oyunudur ve finansal risk içerir.
                </p>

                <h2 className="text-white font-bold text-lg mb-4">3. Premium İçerikler</h2>
                <p className="text-gray-400 mb-6">
                    Bazı içerikler "Yıldız" adı verilen uygulama içi para birimi ile erişilebilir. Satın alınan yıldızlar iade edilemez ve nakde çevrilemez.
                </p>

                <h2 className="text-white font-bold text-lg mb-4">4. Sorumluluk Reddi</h2>
                <p className="text-gray-400 mb-6">
                    Uygulama geliştiricileri, tahminlerin doğruluğu veya kullanıcıların bu tahminlere dayanarak yaptığı bahislerden doğacak kayıplardan sorumlu değildir. Lütfen sorumlu bahis oynayınız.
                </p>

                <h2 className="text-white font-bold text-lg mb-4">5. Değişiklikler</h2>
                <p className="text-gray-400 mb-6">
                    Bu koşullar önceden haber verilmeksizin güncellenebilir. Uygulamayı kullanmaya devam etmeniz, değişiklikleri kabul ettiğiniz anlamına gelir.
                </p>
            </main>
        </div>
    );
}
