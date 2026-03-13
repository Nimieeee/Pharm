import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.benchside.app',
  appName: 'Benchside',
  webDir: 'out',
  server: {
    cleartext: true,
    url: undefined,
    androidScheme: 'https'
  }
};

export default config;
