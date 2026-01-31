import { NavLink } from 'react-router-dom';

const navItems = [
    { path: '/', icon: 'home', label: 'Ana Sayfa' },
    { path: '/stats', icon: 'analytics', label: 'İstatistik' },
    { path: '/wallet', icon: 'account_balance_wallet', label: 'Cüzdan' },
    { path: '/profile', icon: 'person', label: 'Profil' },
];

export function BottomNav() {
    return (
        <nav className="fixed bottom-0 left-0 right-0 bg-background-dark/95 backdrop-blur-xl border-t border-white/5 pt-3 px-6 z-50 safe-area-bottom pb-[calc(20px+env(safe-area-inset-bottom))]">
            <div className="max-w-md mx-auto flex items-center justify-between">
                {navItems.slice(0, 2).map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) =>
                            `flex flex-col items-center gap-1 ${isActive ? 'text-primary' : 'text-gray-500'}`
                        }
                    >
                        {({ isActive }) => (
                            <>
                                <span
                                    className="material-symbols-outlined"
                                    style={isActive ? { fontVariationSettings: "'FILL' 1" } : undefined}
                                >
                                    {item.icon}
                                </span>
                                <span className="text-[10px] font-bold uppercase tracking-tighter">{item.label}</span>
                            </>
                        )}
                    </NavLink>
                ))}

                {/* Center FAB */}
                <div className="relative -top-6">
                    <button className="size-14 bg-primary rounded-full flex items-center justify-center shadow-[0_0_20px_rgba(0,122,92,0.4)] border-4 border-background-dark active:scale-90 transition-transform">
                        <span className="material-symbols-outlined text-white text-3xl">add</span>
                    </button>
                </div>

                {navItems.slice(2).map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) =>
                            `flex flex-col items-center gap-1 ${isActive ? 'text-primary' : 'text-gray-500'}`
                        }
                    >
                        {({ isActive }) => (
                            <>
                                <span
                                    className="material-symbols-outlined"
                                    style={isActive ? { fontVariationSettings: "'FILL' 1" } : undefined}
                                >
                                    {item.icon}
                                </span>
                                <span className="text-[10px] font-bold uppercase tracking-tighter">{item.label}</span>
                            </>
                        )}
                    </NavLink>
                ))}
            </div>
        </nav>
    );
}
