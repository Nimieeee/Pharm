'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { App } from '@capacitor/app';

export default function DeepLinkHandler() {
  const router = useRouter();

  useEffect(() => {
    // Handle deep links when the app is already open
    App.addListener('appUrlOpen', (data: any) => {
      // Example deep link: com.benchside.app://lab?smiles=CC
      // data.url will be the full URL
      const url = new URL(data.url);
      const path = url.pathname;
      const search = url.search;
      
      // Navigate to the appropriate route within the Next.js app
      router.push(`${path}${search}`);
    });

    // Handle initial deep link if the app was closed
    const checkInitialUrl = async () => {
      const launchUrl = await App.getLaunchUrl();
      if (launchUrl) {
        const url = new URL(launchUrl.url);
        router.push(`${url.pathname}${url.search}`);
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
