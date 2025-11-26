/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  // Transpile streamdown for proper ESM handling
  transpilePackages: ['streamdown'],
  experimental: {
    // Optimize package imports
    optimizePackageImports: ['lucide-react', 'framer-motion'],
  },
  webpack: (config, { isServer }) => {
    // Prevent streamdown from being bundled on the server during static generation
    if (isServer) {
      config.externals = config.externals || [];
      // Use a function to handle the external
      const originalExternals = config.externals;
      config.externals = async (context) => {
        const { request } = context;
        // Externalize streamdown on server
        if (request === 'streamdown') {
          return `commonjs ${request}`;
        }
        // Handle other externals
        if (typeof originalExternals === 'function') {
          return originalExternals(context);
        }
        if (Array.isArray(originalExternals)) {
          for (const external of originalExternals) {
            if (typeof external === 'function') {
              const result = await external(context);
              if (result) return result;
            }
          }
        }
        return undefined;
      };
    }
    return config;
  },
}

module.exports = nextConfig
