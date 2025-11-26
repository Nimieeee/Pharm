/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  // Transpile streamdown for proper ESM handling
  transpilePackages: ['streamdown'],
  webpack: (config, { isServer }) => {
    // Prevent streamdown from being bundled on the server
    if (isServer) {
      config.externals = config.externals || [];
      config.externals.push({
        streamdown: 'streamdown',
      });
    }
    return config;
  },
}

module.exports = nextConfig
