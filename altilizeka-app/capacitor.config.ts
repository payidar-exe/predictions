import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.altilizeka.app',
  appName: 'AltılıZeka',
  webDir: 'dist',
  plugins: {
    AdMob: {
      // App IDs
      appIdAndroid: 'ca-app-pub-2094089827700165~7931401187',
      appIdIos: 'ca-app-pub-2094089827700165~6618319516',
    }
  }
};

export default config;
