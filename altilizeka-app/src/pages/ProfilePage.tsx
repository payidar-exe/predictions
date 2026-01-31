import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores';
import { BottomNav } from '../components/BottomNav';

export function ProfilePage() {
    const user = useAuthStore((s) => s.user);
    const signOut = useAuthStore((s) => s.signOut);
    const navigate = useNavigate();

    const handleSignOut = async () => {
        await signOut();
        navigate('/login');
    };

    const menuItems = [
        { icon: 'receipt_long', label: 'Satın Aldığım Kuponlar', path: '/my-coupons' },
        { icon: 'history', label: 'Yıldız Geçmişi', path: '/star-history' },
        { icon: 'notifications', label: 'Bildirim Ayarları', path: '/notifications' },
        { icon: 'help_outline', label: 'Yardım & Destek', path: '/help' },
        { icon: 'info', label: 'Hakkında', path: '/about' },
    ];

    return (
        <div className="min-h-screen bg-background-dark pb-24">
            {/* Header */}
            <header className="pt-12 pb-6 px-6 safe-area-top">
                <h1 className="text-2xl font-bold text-white tracking-tight">Profilim</h1>
            </header>

            {/* User Card */}
            <div className="mx-4 mb-6 bg-card-dark rounded-2xl border border-white/5 overflow-hidden">
                <div className="p-6 flex items-center gap-4">
                    <div className="size-16 rounded-full bg-gradient-to-br from-primary to-accent-gold p-[2px]">
                        <div className="w-full h-full rounded-full bg-background-dark flex items-center justify-center">
                            {user?.avatar_url ? (
                                <img src={user.avatar_url} alt="Avatar" className="w-full h-full rounded-full object-cover" />
                            ) : (
                                <span className="material-symbols-outlined text-3xl text-gray-400">person</span>
                            )}
                        </div>
                    </div>
                    <div className="flex-1">
                        <h2 className="text-xl font-bold text-white">{user?.display_name || 'Misafir'}</h2>
                        <p className="text-gray-400 text-sm">Üyelik: {user?.created_at ? new Date(user.created_at).toLocaleDateString('tr-TR') : '-'}</p>
                    </div>
                    <button className="size-10 rounded-full bg-white/5 flex items-center justify-center hover:bg-white/10 transition-colors">
                        <span className="material-symbols-outlined text-gray-400">edit</span>
                    </button>
                </div>

                {/* Star Balance */}
                <div className="px-6 pb-6">
                    <div className="bg-gradient-to-r from-accent-gold/20 to-accent-gold/5 border border-accent-gold/30 rounded-xl p-4 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <span className="material-symbols-outlined text-accent-gold text-3xl" style={{ fontVariationSettings: "'FILL' 1" }}>
                                stars
                            </span>
                            <div>
                                <p className="text-white text-2xl font-bold">{user?.star_balance ?? 0}</p>
                                <p className="text-gray-400 text-xs">Yıldız Bakiyeniz</p>
                            </div>
                        </div>
                        <Link
                            to="/stars"
                            className="bg-accent-gold hover:bg-accent-gold/90 text-background-dark px-4 py-2 rounded-lg font-bold text-sm flex items-center gap-2 transition-colors"
                        >
                            <span className="material-symbols-outlined text-lg">add</span>
                            <span>Yıldız Al</span>
                        </Link>
                    </div>
                </div>
            </div>

            {/* Menu */}
            <div className="mx-4 bg-card-dark rounded-2xl border border-white/5 overflow-hidden divide-y divide-white/5">
                {menuItems.map((item) => (
                    <Link
                        key={item.path}
                        to={item.path}
                        className="flex items-center gap-4 px-6 py-4 hover:bg-white/5 transition-colors"
                    >
                        <span className="material-symbols-outlined text-gray-400">{item.icon}</span>
                        <span className="flex-1 text-white font-medium">{item.label}</span>
                        <span className="material-symbols-outlined text-gray-600">chevron_right</span>
                    </Link>
                ))}
            </div>

            {/* Logout Button */}
            <div className="mx-4 mt-6">
                <button
                    onClick={handleSignOut}
                    className="w-full bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-400 py-4 rounded-xl font-semibold flex items-center justify-center gap-2 transition-colors"
                >
                    <span className="material-symbols-outlined">logout</span>
                    <span>Çıkış Yap</span>
                </button>
            </div>

            {/* Version */}
            <p className="text-center text-gray-600 text-xs mt-8">AltılıZeka v1.0.0</p>

            <BottomNav />
        </div>
    );
}
