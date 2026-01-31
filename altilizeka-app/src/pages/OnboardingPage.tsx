import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const slides = [
    {
        icon: 'psychology',
        title: 'Yapay Zeka Tahminleri',
        description: 'Kahin v10 AI motoru ile at yarışlarında yüksek isabet oranı yakalayın.',
        color: 'primary',
    },
    {
        icon: 'stars',
        title: 'Yıldız Sistemi',
        description: 'Premium kuponlara erişmek için yıldız satın alın. Her kayıtta 50 yıldız hediye!',
        color: 'accent-gold',
    },
    {
        icon: 'analytics',
        title: 'Detaylı Analizler',
        description: 'Her yarış için AI destekli "Zeka Notları" ile bilinçli kararlar verin.',
        color: 'primary',
    },
];

export function OnboardingPage() {
    const [currentSlide, setCurrentSlide] = useState(0);
    const navigate = useNavigate();

    const handleNext = () => {
        if (currentSlide < slides.length - 1) {
            setCurrentSlide(currentSlide + 1);
        } else {
            // Mark onboarding as complete
            localStorage.setItem('onboarding_complete', 'true');
            navigate('/login');
        }
    };

    const handleSkip = () => {
        localStorage.setItem('onboarding_complete', 'true');
        navigate('/login');
    };

    const slide = slides[currentSlide];
    const isLast = currentSlide === slides.length - 1;

    return (
        <div className="min-h-screen bg-background-dark flex flex-col">
            {/* Skip Button */}
            <header className="pt-12 px-6 flex justify-end safe-area-top">
                <button onClick={handleSkip} className="text-gray-400 text-sm font-medium">
                    Atla
                </button>
            </header>

            {/* Slide Content */}
            <main className="flex-1 flex flex-col items-center justify-center px-8 text-center">
                {/* Icon */}
                <div className={`size-32 rounded-full flex items-center justify-center mb-8 ${slide.color === 'primary' ? 'bg-primary/5' : 'bg-accent-gold/20'
                    }`}>
                    {currentSlide === 0 ? (
                        <img src="/logo.png" alt="Logo" className="w-24 h-24 object-contain drop-shadow-2xl" />
                    ) : (
                        <span
                            className={`material-symbols-outlined text-7xl ${slide.color === 'primary' ? 'text-primary' : 'text-accent-gold'
                                }`}
                            style={{ fontVariationSettings: "'FILL' 1" }}
                        >
                            {slide.icon}
                        </span>
                    )}
                </div>

                {/* Title */}
                <h1 className="text-3xl font-bold text-white tracking-tight mb-4">
                    {slide.title}
                </h1>

                {/* Description */}
                <p className="text-gray-400 text-lg leading-relaxed max-w-sm">
                    {slide.description}
                </p>
            </main>

            {/* Bottom Section */}
            <footer className="px-6 pb-12 safe-area-bottom">
                {/* Dots */}
                <div className="flex items-center justify-center gap-2 mb-8">
                    {slides.map((_, index) => (
                        <button
                            key={index}
                            onClick={() => setCurrentSlide(index)}
                            className={`h-2 rounded-full transition-all ${index === currentSlide
                                ? 'w-8 bg-primary'
                                : 'w-2 bg-white/20'
                                }`}
                        />
                    ))}
                </div>

                {/* Button */}
                <button
                    onClick={handleNext}
                    className="w-full bg-primary hover:bg-primary/90 text-white py-4 rounded-xl font-bold text-lg transition-all flex items-center justify-center gap-2"
                >
                    <span>{isLast ? 'Başla' : 'Devam'}</span>
                    <span className="material-symbols-outlined">
                        {isLast ? 'login' : 'arrow_forward'}
                    </span>
                </button>
            </footer>
        </div>
    );
}
