import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores';

export function SignupPage() {
    const [displayName, setDisplayName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const signUp = useAuthStore((s) => s.signUp);
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        try {
            await signUp(email, password, displayName);
            navigate('/');
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : 'Kayıt başarısız';
            setError(message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-background-dark flex flex-col">
            {/* Header */}
            <header className="pt-12 pb-6 px-6">
                <Link to="/login" className="inline-flex items-center gap-2 text-gray-400 mb-6">
                    <span className="material-symbols-outlined text-xl">arrow_back</span>
                    <span>Geri</span>
                </Link>
                <h1 className="text-3xl font-bold text-white tracking-tight">Hesap Oluştur</h1>
                <p className="text-gray-400 text-sm mt-2">
                    Kayıt ol ve <span className="text-accent-gold font-semibold">50 Yıldız</span> hoşgeldin bonusu kazan!
                </p>
            </header>

            {/* Bonus Card */}
            <div className="mx-6 mb-6 bg-gradient-to-r from-accent-gold/20 to-accent-gold/5 border border-accent-gold/30 rounded-xl p-4 flex items-center gap-4">
                <div className="size-12 bg-accent-gold/20 rounded-full flex items-center justify-center">
                    <span className="material-symbols-outlined text-accent-gold text-2xl" style={{ fontVariationSettings: "'FILL' 1" }}>
                        stars
                    </span>
                </div>
                <div>
                    <p className="text-accent-gold font-bold">50 Yıldız Hediye!</p>
                    <p className="text-gray-400 text-xs">İlk kayıtta hesabına tanımlanır</p>
                </div>
            </div>

            {/* Form */}
            <main className="flex-1 px-6 pb-8">
                <form onSubmit={handleSubmit} className="space-y-4">
                    {error && (
                        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-400 text-sm">
                            {error}
                        </div>
                    )}

                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-2">Adınız</label>
                        <input
                            type="text"
                            value={displayName}
                            onChange={(e) => setDisplayName(e.target.value)}
                            placeholder="Ahmet Yılmaz"
                            required
                            className="w-full bg-card-dark border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-gray-500 focus:outline-none focus:border-primary/50 transition-colors"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-2">E-posta</label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="ornek@email.com"
                            required
                            className="w-full bg-card-dark border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-gray-500 focus:outline-none focus:border-primary/50 transition-colors"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-2">Şifre</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="En az 6 karakter"
                            required
                            minLength={6}
                            className="w-full bg-card-dark border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-gray-500 focus:outline-none focus:border-primary/50 transition-colors"
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={isLoading}
                        className="w-full bg-primary hover:bg-primary/90 disabled:opacity-50 text-white py-4 rounded-xl font-bold text-lg transition-all mt-6 flex items-center justify-center gap-2"
                    >
                        {isLoading ? (
                            <div className="size-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        ) : (
                            <>
                                <span>Kayıt Ol</span>
                                <span className="material-symbols-outlined">person_add</span>
                            </>
                        )}
                    </button>
                </form>

                {/* Login Link */}
                <p className="text-center text-gray-400 mt-8">
                    Zaten hesabın var mı?{' '}
                    <Link to="/login" className="text-primary font-semibold">
                        Giriş Yap
                    </Link>
                </p>
            </main>

            {/* Footer */}
            <footer className="px-6 pb-8 text-center">
                <p className="text-[11px] text-gray-600">
                    Kayıt olarak <span className="text-gray-500">Kullanım Koşulları</span> ve{' '}
                    <span className="text-gray-500">Gizlilik Politikası</span>'nı kabul etmiş olursunuz.
                </p>
            </footer>
        </div>
    );
}
