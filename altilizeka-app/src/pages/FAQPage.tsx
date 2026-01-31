import { Link } from 'react-router-dom';
import { BottomNav } from '../components/BottomNav';

interface FAQItem {
    question: string;
    answer: string;
}

const faqItems: FAQItem[] = [
    {
        question: "AltılıZeka nasıl çalışıyor?",
        answer: "AltılıZeka, yapay zeka modelimiz Kahin v10 kullanarak at yarışı tahminleri üretir. Model, atların geçmiş performansları, jokey istatistikleri, pist koşulları ve birçok faktörü analiz ederek tahminlerini oluşturur."
    },
    {
        question: "Yıldız nedir ve nasıl kullanılır?",
        answer: "Yıldızlar, uygulama içi para biriminizdir. Premium kuponların tamamını açmak için yıldız harcarsınız. Yıldız satın alabilir veya reklam izleyerek ücretsiz yıldız kazanabilirsiniz."
    },
    {
        question: "Reklam izleyerek ne kazanırım?",
        answer: "Her kupon için 1 koşunun favorisini ücretsiz görebilirsiniz. Bunun için kısa bir reklam izlemeniz yeterli. Tüm koşuları görmek için yıldız kullanmanız gerekir."
    },
    {
        question: "Tahminler ne kadar doğru?",
        answer: "Kahin v10 AI modelimiz, geçmiş verilere göre ortalama %35 oranında 6/6 isabet sağlamaktadır. Ancak at yarışı doğası gereği belirsizlik içerir ve geçmiş performans gelecek sonuçları garanti etmez."
    },
    {
        question: "Kuponlar ne zaman yayınlanıyor?",
        answer: "Günün kuponları her gün saat 10:00'da yayınlanır. Yarış günlerinde ilgili hipodromlar için tahminler oluşturulur."
    },
    {
        question: "Satın aldığım yıldızlar iade edilir mi?",
        answer: "Yıldız satın alımları iade edilmez. Ancak teknik bir sorun yaşarsanız destek ekibimizle iletişime geçebilirsiniz."
    },
    {
        question: "Hesabımı nasıl silebilirim?",
        answer: "Profil sayfasından 'Hesabı Sil' seçeneğine tıklayarak hesabınızı kalıcı olarak silebilirsiniz. Bu işlem geri alınamaz."
    },
    {
        question: "Uygulama hangi şehirleri destekliyor?",
        answer: "Türkiye'deki tüm hipodromları destekliyoruz: İstanbul, Ankara, İzmir, Bursa, Adana, Elazığ, Şanlıurfa, Diyarbakır ve diğerleri."
    }
];

export function FAQPage() {
    return (
        <div className="min-h-screen bg-background-dark pb-24">
            {/* Header */}
            <header className="pt-12 pb-4 px-6 safe-area-top flex items-center gap-4">
                <Link to="/profile" className="size-10 flex items-center justify-center rounded-full bg-white/5 hover:bg-white/10 transition-colors">
                    <span className="material-symbols-outlined text-white">arrow_back</span>
                </Link>
                <div>
                    <h1 className="text-2xl font-bold text-white tracking-tight">Sık Sorulan Sorular</h1>
                    <p className="text-gray-400 text-sm mt-0.5">Yardım ve destek</p>
                </div>
            </header>

            <main className="px-4 space-y-3">
                {faqItems.map((item, index) => (
                    <details key={index} className="group bg-card-dark border border-white/5 rounded-xl overflow-hidden">
                        <summary className="p-4 cursor-pointer list-none flex items-center justify-between hover:bg-white/5 transition-colors">
                            <span className="text-white font-medium pr-4">{item.question}</span>
                            <span className="material-symbols-outlined text-gray-400 group-open:rotate-180 transition-transform">
                                expand_more
                            </span>
                        </summary>
                        <div className="px-4 pb-4 pt-0 border-t border-white/5">
                            <p className="text-gray-400 text-sm leading-relaxed">{item.answer}</p>
                        </div>
                    </details>
                ))}

                {/* Contact Section */}
                <div className="bg-primary/10 border border-primary/20 rounded-xl p-4 mt-6">
                    <div className="flex items-start gap-3">
                        <span className="material-symbols-outlined text-primary">support_agent</span>
                        <div>
                            <h3 className="text-white font-bold text-sm">Başka sorunuz mu var?</h3>
                            <p className="text-gray-400 text-xs mt-1">
                                Destek için: <span className="text-primary">destek@altilizeka.com</span>
                            </p>
                        </div>
                    </div>
                </div>
            </main>

            <BottomNav />
        </div>
    );
}
