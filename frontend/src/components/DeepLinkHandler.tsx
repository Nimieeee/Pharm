'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { App } from '@capacitor/app';

export default function DeepLinkHandler() {
  const router = useRouter();

  useEffect(() => {
    // Handle deep links when the app is already open
    App.addListener('appUrlOpen', (data: any) => {
      try {
        if (!data?.url || typeof data.url !== 'string') {
          console.warn('Invalid deep link data received:', data);
          return;
        }
        const url = new URL(data.url);
        const path = url.pathname;
        const search = url.search;

        // Navigate to the appropriate route within the Next.js app
        router.push(`${path}${search}`);
      } catch (e) {
        console.error('Failed to process deep link:', e);
      }
    });

    // Handle initial deep link if the app was closed
    const checkInitialUrl = async () => {
      try {
        const launchUrl = await App.getLaunchUrl();
        if (!launchUrl?.url || typeof launchUrl.url !== 'string') {
          return;  // No initial URL to process
        }
        const url = new URL(launchUrl.url);
        router.push(`${url.pathname}${url.search}`);
      } catch (e) {
        console.error('Failed to process initial URL:', e);
      }
    };

    checkInitialUrl();

    // Cleanup listeners
    return () => {
      App.removeAllListeners();
    };
  }, [router]);

  return null; // This component doesn't render anything
}
