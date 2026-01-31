import { Link } from 'react-router-dom';
import { useAuthStore } from '../stores';

export function TopBar() {
    const user = useAuthStore((s) => s.user);

    return (
        <header className="fixed top-0 left-0 right-0 z-50 bg-background-dark/80 backdrop-blur-md border-b border-white/5 pt-[env(safe-area-inset-top)]">
            <div className="flex items-center justify-between px-4 h-16 max-w-md mx-auto">
                {/* User Info */}
                <div className="flex items-center gap-3">
                    <Link to="/profile" className="size-10 rounded-full bg-gradient-to-tr from-primary to-accent-gold p-[2px]">
                        <div className="w-full h-full rounded-full bg-background-dark flex items-center justify-center overflow-hidden">
                            {user?.avatar_url ? (
                                <img src={user.avatar_url} alt="Avatar" className="w-full h-full object-cover" />
                            ) : (
                                <span className="material-symbols-outlined text-white">person</span>
                            )}
                        </div>
                    </Link>
                    <div>
                        <p className="text-[10px] text-gray-400 font-medium uppercase tracking-wider">Merhaba</p>
                        <p className="text-sm font-bold">{user?.display_name || 'Misafir'}</p>
                    </div>
                </div>

                {/* Star Balance */}
                <Link to="/stars" className="bg-white/5 border border-white/10 rounded-full px-3 py-1.5 flex items-center gap-2">
                    <span
                        className="material-symbols-outlined text-accent-gold text-[18px] gold-glow"
                        style={{ fontVariationSettings: "'FILL' 1" }}
                    >
                        stars
                    </span>
                    <span className="text-sm font-bold text-accent-gold tracking-tight">
                        {user?.star_balance ?? 0} Yıldız
                    </span>
                </Link>
            </div>
        </header>
    );
}
