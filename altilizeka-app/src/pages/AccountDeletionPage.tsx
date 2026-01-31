import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { supabase } from '../lib/supabase';
import { useAuthStore } from '../stores';
import { BottomNav } from '../components/BottomNav';

export function AccountDeletionPage() {
    const navigate = useNavigate();
    const { user, signOut } = useAuthStore();
    const [isDeleting, setIsDeleting] = useState(false);
    const [confirmText, setConfirmText] = useState('');
    const [error, setError] = useState<string | null>(null);

    const canDelete = confirmText === 'SİL';

    const handleDeleteAccount = async () => {
        if (!user || !canDelete) return;

        setIsDeleting(true);
        setError(null);

        try {
            // Delete user profile data
            const { error: profileError } = await supabase
                .from('profiles')
                .delete()
                .eq('id', user.id);

            if (profileError) throw profileError;

            // Delete user purchases
            await supabase
                .from('user_purchases')
                .delete()
                .eq('user_id', user.id);

            // Sign out the user
            await supabase.auth.signOut();

            // Clear local state
            await signOut();

            // Redirect to home
            navigate('/');

        } catch (err) {
            console.error('Account deletion error:', err);
            setError('Hesap silinirken bir hata oluştu. Lütfen tekrar deneyin.');
            setIsDeleting(false);
        }
    };

    return (
        <div className="min-h-screen bg-background-dark pb-24">
            {/* Header */}
            <header className="pt-12 pb-4 px-6 safe-area-top flex items-center gap-4">
                <Link to="/profile" className="size-10 flex items-center justify-center rounded-full bg-white/5 hover:bg-white/10 transition-colors">
                    <span className="material-symbols-outlined text-white">arrow_back</span>
                </Link>
                <div>
                    <h1 className="text-2xl font-bold text-white tracking-tight">Hesabı Sil</h1>
                    <p className="text-gray-400 text-sm mt-0.5">Kalıcı hesap silme</p>
                </div>
            </header>

            <main className="px-4 space-y-6">
                {/* Warning Card */}
                <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-5">
                    <div className="flex items-start gap-3">
                        <span className="material-symbols-outlined text-red-400 text-2xl">warning</span>
                        <div>
                            <h3 className="text-red-400 font-bold">Dikkat!</h3>
                            <p className="text-gray-300 text-sm mt-2 leading-relaxed">
                                Hesabınızı sildiğinizde aşağıdaki veriler <strong>kalıcı olarak</strong> silinecektir:
                            </p>
                        </div>
                    </div>
                </div>

                {/* What will be deleted */}
                <div className="bg-card-dark border border-white/5 rounded-xl p-5 space-y-3">
                    <h3 className="text-white font-bold text-sm">Silinecek Veriler</h3>

                    <div className="space-y-2">
                        {[
                            { icon: 'person', text: 'Profil bilgileriniz' },
                            { icon: 'stars', text: 'Yıldız bakiyeniz' },
                            { icon: 'receipt_long', text: 'Satın alma geçmişiniz' },
                            { icon: 'confirmation_number', text: 'Açtığınız kuponlar' },
                        ].map((item, i) => (
                            <div key={i} className="flex items-center gap-3 text-gray-400">
                                <span className="material-symbols-outlined text-red-400 text-lg">{item.icon}</span>
                                <span className="text-sm">{item.text}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Confirmation Input */}
                <div className="bg-card-dark border border-white/5 rounded-xl p-5 space-y-4">
                    <h3 className="text-white font-bold text-sm">Onay</h3>
                    <p className="text-gray-400 text-sm">
                        Hesabınızı silmek için aşağıya <strong className="text-red-400">SİL</strong> yazın:
                    </p>
                    <input
                        type="text"
                        value={confirmText}
                        onChange={(e) => setConfirmText(e.target.value.toUpperCase())}
                        placeholder="SİL"
                        className="w-full bg-black/30 border border-white/10 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-red-500/50"
                    />
                </div>

                {/* Error Message */}
                {error && (
                    <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-red-400 text-sm">
                        {error}
                    </div>
                )}

                {/* Delete Button */}
                <button
                    onClick={handleDeleteAccount}
                    disabled={!canDelete || isDeleting}
                    className={`w-full py-4 rounded-xl font-bold text-lg flex items-center justify-center gap-2 transition-all ${canDelete
                        ? 'bg-red-500 hover:bg-red-600 text-white'
                        : 'bg-gray-700 text-gray-500 cursor-not-allowed'
                        }`}
                >
                    {isDeleting ? (
                        <>
                            <div className="size-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                            Siliniyor...
                        </>
                    ) : (
                        <>
                            <span className="material-symbols-outlined">delete_forever</span>
                            Hesabımı Kalıcı Olarak Sil
                        </>
                    )}
                </button>

                {/* Cancel Link */}
                <Link
                    to="/profile"
                    className="block text-center text-gray-400 hover:text-white transition-colors text-sm"
                >
                    Vazgeç
                </Link>
            </main>

            <BottomNav />
        </div>
    );
}
