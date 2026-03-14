'use client';

import { useAuth } from '@/lib/auth-context';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { motion } from 'framer-motion';
import { Loader2 } from 'lucide-react';

interface AuthGuardProps {
  children: React.ReactNode;
}

/**
 * Reusable auth guard wrapper.
 * Redirects to /login if the user is not authenticated.
 * Shows a loading spinner while auth state is being resolved.
 */
export default function AuthGuard({ children }: AuthGuardProps) {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) {
      // Check localStorage as fallback (token might exist but user hasn't been fetched yet)
      const token = localStorage.getItem('token');
      if (!token) {
        router.replace('/login');
      }
    }
  }, [user, isLoading, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex flex-col items-center gap-4"
        >
          <Loader2 className="w-8 h-8 animate-spin text-orange-500" />
          <p className="text-sm text-foreground-muted">Loading...</p>
        </motion.div>
      </div>
    );
  }

  // If no user and no token, don't render (redirect will happen via useEffect)
  if (!user && !localStorage.getItem('token')) {
    return null;
  }

  return <>{children}</>;
}
