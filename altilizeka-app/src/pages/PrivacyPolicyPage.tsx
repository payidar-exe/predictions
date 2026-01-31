import { Link } from 'react-router-dom';

export function PrivacyPolicyPage() {
    return (
        <div className="min-h-screen bg-background-dark pb-12">
            {/* Header */}
            <header className="sticky top-0 z-40 bg-background-dark/95 ios-blur border-b border-white/5 safe-area-top">
                <div className="flex items-center gap-4 px-4 py-3">
                    <Link to="/login" className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors">
                        <span className="material-symbols-outlined">arrow_back</span>
                        <span className="text-sm font-medium">Geri</span>
                    </Link>
                    <h1 className="text-lg font-bold text-white text-center flex-1 pr-16">Gizlilik Politikası</h1>
                </div>
            </header>

            <main className="px-6 py-8 prose prose-invert prose-sm max-w-none">
                <h2 className="text-white font-bold text-lg mb-4">1. Giriş</h2>
                <p className="text-gray-400 mb-6">
                    AltılıZeka ("Uygulama") olarak gizliliğinize önem veriyoruz. Bu Gizlilik Politikası, kişisel verilerinizin nasıl toplandığını, kullanıldığını ve korunduğunu açıklar.
                </p>

                <h2 className="text-white font-bold text-lg mb-4">2. Toplanan Veriler</h2>
                <p className="text-gray-400 mb-4">
                    Uygulamayı kullanırken aşağıdaki bilgileri toplayabiliriz:
                </p>
                <ul className="list-disc pl-5 text-gray-400 mb-6 space-y-2">
                    <li><strong>Hesap Bilgileri:</strong> Ad, soyad, e-posta adresi ve profil fotoğrafı (Google/Apple ile giriş yapıldığında).</li>
                    <li><strong>İşlem Bilgileri:</strong> Satın alma geçmişi, yıldız bakiyesi ve kupon kullanım detayları.</li>
                    <li><strong>Cihaz Bilgileri:</strong> Cihaz modeli, işletim sistemi sürümü ve uygulama kullanım istatistikleri.</li>
                </ul>

                <h2 className="text-white font-bold text-lg mb-4">3. Verilerin Kullanımı</h2>
                <p className="text-gray-400 mb-6">
                    Toplanan veriler şu amaçlarla kullanılır:
                    <br />• Hizmetlerimizi sunmak ve iyileştirmek
                    <br />• Ödeme işlemlerini gerçekleştirmek
                    <br />• Kişiselleştirilmiş tahminler sunmak
                    <br />• Hesap güvenliğini sağlamak
                </p>

                <h2 className="text-white font-bold text-lg mb-4">4. Veri Güvenliği</h2>
                <p className="text-gray-400 mb-6">
                    Verileriniz endüstri standardı güvenlik önlemleri (SSL şifreleme, güvenli sunucular) ile korunmaktadır. Ödeme işlemleri App Store ve Google Play üzerinden güvenli bir şekilde gerçekleştirilir.
                </p>

                <h2 className="text-white font-bold text-lg mb-4">5. Hesabın Silinmesi</h2>
                <p className="text-gray-400 mb-6">
                    Hesabınızı ve tüm verilerinizi dilediğiniz zaman uygulama içi ayarlardan veya <strong>destek@altilizeka.com</strong> adresine e-posta göndererek silebilirsiniz.
                </p>

                <h2 className="text-white font-bold text-lg mb-4">6. İletişim</h2>
                <p className="text-gray-400">
                    Bu politika hakkında sorularınız için bizimle iletişime geçebilirsiniz:<br />
                    <a href="mailto:destek@altilizeka.com" className="text-primary hover:underline">destek@altilizeka.com</a>
                </p>
            </main>
        </div>
    );
}
