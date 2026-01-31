import type { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuthStore } from '../stores';

interface AuthGuardProps {
    children: ReactNode;
    requireAuth?: boolean;
}

/**
 * AuthGuard component for protecting routes
 * - requireAuth=true: Redirects to /login if not authenticated
 * - requireAuth=false: Redirects to / if already authenticated (for login/signup pages)
 */
export function AuthGuard({ children, requireAuth = true }: AuthGuardProps) {
    const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
    const isLoading = useAuthStore((s) => s.isLoading);

    // Show loading while checking auth state
    if (isLoading) {
        return (
            <div className="min-h-screen bg-background-dark flex items-center justify-center">
                <div className="flex flex-col items-center gap-4">
                    <div className="size-12 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                    <p className="text-gray-400 text-sm">Yükleniyor...</p>
                </div>
            </div>
        );
    }

    if (requireAuth && !isAuthenticated) {
        return <Navigate to="/login" replace />;
    }

    if (!requireAuth && isAuthenticated) {
        return <Navigate to="/" replace />;
    }

    return <>{children}</>;
}
