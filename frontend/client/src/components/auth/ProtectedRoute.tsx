/**
 * ProtectedRoute Component
 *
 * A wrapper component that ensures only authenticated users can access
 * certain routes. Redirects unauthenticated users to sign-in.
 */

import { useAuth, useUser } from '@clerk/clerk-react';
import { ReactNode } from 'react';
import { Loader2, Lock, ShieldX } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { hasRole } from '@/lib/clerk';

interface ProtectedRouteProps {
  children: ReactNode;
  fallback?: ReactNode;
  requireRole?: string;
  redirectTo?: string;
}

export function ProtectedRoute({
  children,
  fallback,
  requireRole,
  redirectTo = '/sign-in'
}: ProtectedRouteProps) {
  const { isLoaded, isSignedIn } = useAuth();
  const { user, isLoaded: userLoaded } = useUser();

  // Show loading state while Clerk is initializing
  if (!isLoaded || !userLoaded) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // Show sign-in prompt for unauthenticated users
  if (!isSignedIn) {
    if (fallback) {
      return <>{fallback}</>;
    }

    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center max-w-md mx-auto p-6">
          <Lock className="h-12 w-12 mx-auto mb-4 text-gray-400" />
          <h2 className="text-2xl font-semibold mb-2">Authentication Required</h2>
          <p className="text-gray-600 mb-6">
            You need to sign in to access this page.
          </p>
          <Button
            onClick={() => window.location.href = redirectTo}
            className="w-full"
          >
            Sign In to Continue
          </Button>
        </div>
      </div>
    );
  }

  // Check role-based access control
  if (requireRole && !hasRole(user, requireRole)) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center max-w-md mx-auto p-6">
          <Lock className="h-12 w-12 mx-auto mb-4 text-gray-400" />
          <h2 className="text-2xl font-semibold mb-2">Unauthorized</h2>
          <p className="text-gray-600">
            You need the <span className="font-semibold">{requireRole}</span> role to access this page.
          </p>
        </div>
      </div>
    );
  }

  // Render protected content for authenticated users
  return <>{children}</>;
}

/**
 * Hook for checking if current route requires authentication
 */
export function useRequireAuth() {
  const { isLoaded, isSignedIn } = useAuth();

  return {
    isLoaded,
    isAuthenticated: isSignedIn,
    requiresAuth: !isLoaded || !isSignedIn
  };
}

/**
 * Higher-order component for protecting routes
 */
export function withAuth<P extends object>(
  Component: React.ComponentType<P>,
  options?: Omit<ProtectedRouteProps, 'children'>
) {
  return function AuthenticatedComponent(props: P) {
    return (
      <ProtectedRoute {...options}>
        <Component {...props} />
      </ProtectedRoute>
    );
  };
}
