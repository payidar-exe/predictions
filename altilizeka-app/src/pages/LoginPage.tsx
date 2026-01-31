import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores';

export function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const signIn = useAuthStore((s) => s.signIn);
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        try {
            await signIn(email, password);
            navigate('/');
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : 'Giriş başarısız';
            setError(message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-background-dark flex flex-col">
            {/* Header */}
            <header className="pt-12 pb-8 px-6 text-center">
                <div className="size-24 mx-auto mb-6 bg-transparent flex items-center justify-center">
                    <img src="/logo.png" alt="AltılıZeka Logo" className="w-full h-full object-contain drop-shadow-[0_0_15px_rgba(0,122,92,0.5)]" />
                </div>
                <h1 className="text-3xl font-bold text-white tracking-tight">AltılıZeka</h1>
                <p className="text-gray-400 text-sm mt-2">Yapay Zeka Destekli At Yarışı Tahminleri</p>
            </header>

            {/* Form */}
            <main className="flex-1 px-6 pb-8">
                <form onSubmit={handleSubmit} className="space-y-4">
                    {error && (
                        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-400 text-sm">
                            {error}
                        </div>
                    )}

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
                            placeholder="••••••••"
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
                                <span>Giriş Yap</span>
                                <span className="material-symbols-outlined">login</span>
                            </>
                        )}
                    </button>
                </form>

                {/* Divider */}
                <div className="flex items-center gap-4 my-8">
                    <div className="flex-1 h-px bg-white/10" />
                    <span className="text-gray-500 text-sm">veya</span>
                    <div className="flex-1 h-px bg-white/10" />
                </div>

                {/* Social Login */}
                <div className="space-y-3">
                    <button className="w-full bg-white hover:bg-gray-100 text-gray-900 py-3 rounded-xl font-semibold flex items-center justify-center gap-3 transition-colors">
                        <svg className="size-5" viewBox="0 0 24 24">
                            <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                            <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                            <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                            <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                        </svg>
                        <span>Google ile Giriş Yap</span>
                    </button>

                    <button className="w-full bg-black hover:bg-gray-900 text-white py-3 rounded-xl font-semibold flex items-center justify-center gap-3 transition-colors border border-white/10">
                        <svg className="size-5" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z" />
                        </svg>
                        <span>Apple ile Giriş Yap</span>
                    </button>
                </div>

                {/* Register Link */}
                <p className="text-center text-gray-400 mt-8">
                    Hesabın yok mu?{' '}
                    <Link to="/signup" className="text-primary font-semibold">
                        Kayıt Ol
                    </Link>
                </p>
            </main>

            {/* Footer */}
            <footer className="px-6 pb-8 text-center">
                <p className="text-[11px] text-gray-600">
                    Giriş yaparak <span className="text-gray-500">Kullanım Koşulları</span> ve{' '}
                    <span className="text-gray-500">Gizlilik Politikası</span>'nı kabul etmiş olursunuz.
                </p>
            </footer>
        </div>
    );
}
