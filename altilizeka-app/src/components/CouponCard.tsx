import type { Coupon } from '../lib/supabase';

interface CouponCardProps {
    coupon: Coupon;
    isUnlocked?: boolean;
}

const getCityImage = (cityString: string) => {
    const city = cityString.toLowerCase();
    if (city.includes('istanbul')) return '/cities/istanbul.png';
    if (city.includes('ankara')) return '/cities/ankara.png';
    if (city.includes('bursa')) return '/cities/bursa.png';
    if (city.includes('izmir')) return '/cities/izmir.png';
    return '/cities/istanbul.png';
};

export function FreeCouponCard({ coupon }: CouponCardProps) {
    const cityImage = getCityImage(coupon.city);

    return (
        <div className="group relative overflow-hidden rounded-xl bg-card-dark border border-white/5 active:scale-[0.98] transition-all duration-200 shadow-lg shadow-black/20 h-28">
            <div className="absolute inset-0">
                <img src={cityImage} alt={coupon.city} className="w-full h-full object-cover opacity-60 group-hover:scale-105 transition-transform duration-700" />
                <div className="absolute inset-0 bg-gradient-to-r from-black via-black/80 to-transparent" />
            </div>

            <div className="relative h-full flex items-center justify-between p-4">
                <div className="flex flex-col justify-center gap-1">
                    <div className="flex items-center gap-2">
                        <span className="bg-primary/90 text-white text-[10px] font-bold px-2 py-0.5 rounded shadow-sm backdrop-blur-sm border border-white/10">
                            ÜCRETSİZ
                        </span>
                        <span className="text-gray-300 text-[10px] uppercase font-medium tracking-wide">
                            {coupon.city}
                        </span>
                    </div>
                    <div>
                        <h3 className="text-lg font-bold text-white leading-tight">
                            {coupon.title}
                        </h3>
                        <p className="text-gray-400 text-xs mt-0.5">{coupon.subtitle}</p>
                    </div>
                </div>

                <div className="size-8 rounded-full bg-white/10 backdrop-blur-md flex items-center justify-center border border-white/10 group-hover:bg-primary group-hover:border-primary/50 transition-colors">
                    <span className="material-symbols-outlined text-white text-lg">arrow_forward</span>
                </div>
            </div>
        </div>
    );
}

export function PremiumCouponCard({ coupon, isUnlocked = false }: CouponCardProps) {
    const cityImage = getCityImage(coupon.city);

    return (
        <div className={`group relative overflow-hidden rounded-xl border active:scale-[0.98] transition-all duration-200 shadow-lg h-28
            ${isUnlocked ? 'border-green-500/30 shadow-green-500/5' : 'border-accent-gold/30 shadow-accent-gold/5'}`}>
            {/* Background Image */}
            <div className="absolute inset-0">
                <img src={cityImage} alt={coupon.city} className="w-full h-full object-cover opacity-60 group-hover:scale-105 transition-transform duration-700" />
                <div className="absolute inset-0 bg-gradient-to-r from-background-dark via-background-dark/90 to-transparent" />
            </div>

            {/* Unlocked Badge */}
            {isUnlocked && (
                <div className="absolute top-2 right-2 bg-green-500/20 border border-green-500/30 px-2 py-0.5 rounded flex items-center gap-1 z-10">
                    <span className="material-symbols-outlined text-green-400 text-xs" style={{ fontVariationSettings: "'FILL' 1" }}>lock_open</span>
                    <span className="text-green-400 text-[10px] font-bold">AÇILDI</span>
                </div>
            )}

            {/* Glowing Border Effect */}
            <div className={`absolute inset-0 border rounded-xl pointer-events-none ${isUnlocked ? 'border-green-500/20' : 'border-accent-gold/20'}`} />

            <div className="relative h-full flex items-center justify-between p-4">
                {/* Left Content */}
                <div className="flex flex-col justify-center gap-1">
                    <div className="flex items-center gap-2">
                        {!isUnlocked && (
                            <div className="flex items-center gap-1 bg-accent-gold/20 backdrop-blur-sm border border-accent-gold/20 px-2 py-0.5 rounded">
                                <span className="material-symbols-outlined text-accent-gold text-[10px]" style={{ fontVariationSettings: "'FILL' 1" }}>stars</span>
                                <span className="text-accent-gold text-[10px] font-bold">{coupon.star_cost} Yıldız</span>
                            </div>
                        )}
                        <span className="text-gray-300 text-[10px] uppercase font-medium tracking-wide">
                            {coupon.city}
                        </span>
                    </div>
                    <div>
                        <h3 className={`text-lg font-bold leading-tight bg-clip-text text-transparent bg-gradient-to-r 
                            ${isUnlocked ? 'from-green-400 via-white to-green-400' : 'from-accent-gold via-white to-accent-gold'}`}>
                            {coupon.title}
                        </h3>
                        {/* Show TUTAR only when unlocked */}
                        {isUnlocked ? (
                            <p className="text-green-400/70 text-xs mt-0.5 font-medium">{coupon.subtitle}</p>
                        ) : (
                            <p className="text-gray-500 text-xs mt-0.5 italic">Kupon maliyetini görmek için açın</p>
                        )}
                    </div>
                </div>

                {/* Right Lock/Arrow */}
                <div className={`size-8 rounded-full backdrop-blur-md flex items-center justify-center border transition-colors
                    ${isUnlocked
                        ? 'bg-green-500/10 border-green-500/30 group-hover:bg-green-500 group-hover:text-white'
                        : 'bg-accent-gold/10 border-accent-gold/30 group-hover:bg-accent-gold group-hover:text-black'}`}>
                    <span className={`material-symbols-outlined text-lg transition-colors
                        ${isUnlocked ? 'text-green-400 group-hover:text-white' : 'text-accent-gold group-hover:text-black'}`}
                        style={{ fontVariationSettings: "'FILL' 1" }}>
                        {isUnlocked ? 'arrow_forward' : 'lock'}
                    </span>
                </div>
            </div>
        </div>
    );
}
