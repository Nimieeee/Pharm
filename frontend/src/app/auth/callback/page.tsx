'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@supabase/supabase-js';
import { useAuth } from '@/lib/auth-context';
import { Loader2 } from 'lucide-react';

const supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);

const API_BASE_URL = typeof window !== 'undefined' && window.location.hostname !== 'localhost'
    ? ''
    : 'http://localhost:8000';

export default function AuthCallback() {
    const router = useRouter();
    const { logout } = useAuth(); // We'll need to manually set the token, but using context might be better
    const [status, setStatus] = useState('Verifying...');

    useEffect(() => {
        const handleCallback = async () => {
            try {
                // 1. Get the session from Supabase (from URL hash)
                const { data, error } = await supabase.auth.getSession();

                if (error) {
                    console.error("Supabase Session Error:", error);
                    throw error;
                }

                if (!data.session) {
                    // Try to exchange code if present (PKCE flow) as fallback, 
                    // though signInWithOAuth usually uses hash fragment by default in older libs, 
                    // newer ones use code. Let's see what happens.
                    // If no session found, maybe redirect to login
                    router.push('/login?error=No+session+found');
                    return;
                }

                // 2. We have a Supabase session. Now exchange it for our Backend JWT.
                setStatus('Syncing with server...');

                const res = await fetch(`${API_BASE_URL}/api/v1/auth/google-login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        access_token: data.session.access_token
                    })
                });

                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.detail || 'Backend sync failed');
                }

                const tokens = await res.json();

                // 3. Store tokens and redirect
                localStorage.setItem('token', tokens.access_token);
                localStorage.setItem('refreshToken', tokens.refresh_token);
                // Trigger a hard reload or context update? 
                // Since we're not inside the AuthContext provider scope deeply enough or 
                // we want a clean state, reloading /chat is safest.
                // Or better: dispatch a storage event or just push to /chat and let the 
                // AuthContext in /app/layout initialize from storage.

                // Force AuthContext to reload user by dispatching specific event or just navigating
                // The simplest way to ensure context updates is to reload the page or 
                // rely on AuthContext's mount check (which runs on initial load).
                // Getting `login()` from context and calling it with tokens would be ideal but 
                // our `login` function takes email/password.

                // We'll just redirect to chat. The AuthProvider runs `checkUser` on mount/route change 
                // or we can manually reload.
                window.location.href = '/chat';

            } catch (err: any) {
                console.error('Callback error:', err);
                router.push(`/login?error=${encodeURIComponent(err.message)}`);
            }
        };

        handleCallback();
    }, [router]);

    return (
        <div className="min-h-screen flex items-center justify-center bg-[var(--background)]">
            <div className="flex flex-col items-center gap-4">
                <Loader2 size={32} className="animate-spin text-indigo-500" />
                <p className="text-[var(--text-secondary)]">{status}</p>
            </div>
        </div>
    );
}
