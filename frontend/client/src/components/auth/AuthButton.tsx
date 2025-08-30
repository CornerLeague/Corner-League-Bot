/**
 * AuthButton Component
 *
 * A smart authentication button that displays different UI based on the user's
 * authentication state. Shows sign-in/sign-up buttons for unauthenticated users
 * and a user menu for authenticated users.
 */

import { useAuth, useUser, SignInButton, SignUpButton, UserButton } from '@clerk/clerk-react';
import { Button } from '@/components/ui/button';
import { Loader2, User, LogIn, UserPlus } from 'lucide-react';

interface AuthButtonProps {
  variant?: 'default' | 'outline' | 'ghost';
  size?: 'sm' | 'default' | 'lg';
  showSignUp?: boolean;
  className?: string;
}

export function AuthButton({
  variant = 'default',
  size = 'default',
  showSignUp = true,
  className = ''
}: AuthButtonProps) {
  const { isLoaded, isSignedIn } = useAuth();
  const { user } = useUser();

  // Show loading state while Clerk is initializing
  if (!isLoaded) {
    return (
      <Button variant={variant} size={size} disabled className={className}>
        <Loader2 className="h-4 w-4 animate-spin mr-2" />
        Loading...
      </Button>
    );
  }

  // Show UserButton for authenticated users
  if (isSignedIn && user) {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        <span className="text-sm text-gray-600 hidden sm:inline">
          Welcome, {user.firstName || user.username || 'User'}
        </span>
        <UserButton
          appearance={{
            elements: {
              avatarBox: 'h-8 w-8',
              userButtonPopoverCard: 'shadow-lg border border-gray-200',
              userButtonPopoverActionButton: 'hover:bg-gray-50',
            }
          }}
          showName={false}
          userProfileMode="navigation"
          userProfileUrl="/profile"
        />
      </div>
    );
  }

  // Show sign-in/sign-up buttons for unauthenticated users
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <SignInButton forceRedirectUrl="/sign-in">
        <Button variant="outline" size={size}>
          <LogIn className="h-4 w-4 mr-2" />
          Sign In
        </Button>
      </SignInButton>

      {showSignUp && (
        <SignUpButton forceRedirectUrl="/sign-up">
          <Button variant={variant} size={size}>
            <UserPlus className="h-4 w-4 mr-2" />
            Sign Up
          </Button>
        </SignUpButton>
      )}
    </div>
  );
}

/**
 * Compact AuthButton for mobile or space-constrained layouts
 */
export function CompactAuthButton({ className = '' }: { className?: string }) {
  const { isLoaded, isSignedIn } = useAuth();
  const { user } = useUser();

  if (!isLoaded) {
    return (
      <Button variant="ghost" size="sm" disabled className={className}>
        <Loader2 className="h-4 w-4 animate-spin" />
      </Button>
    );
  }

  if (isSignedIn && user) {
    return (
      <UserButton
        appearance={{
          elements: {
            avatarBox: 'h-7 w-7',
          }
        }}
        showName={false}
      />
    );
  }

  return (
    <SignInButton mode="modal">
      <Button variant="ghost" size="sm" className={className}>
        <User className="h-4 w-4" />
      </Button>
    </SignInButton>
  );
}
