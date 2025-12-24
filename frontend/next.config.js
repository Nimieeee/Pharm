/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  experimental: {
    // Optimize package imports
    optimizePackageImports: ['lucide-react', 'framer-motion'],
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://164.68.122.165/api/:path*', // Proxy to Contabo VPS
      },
      {
        source: '/docs',
        destination: 'http://164.68.122.165/docs', // Proxy docs
      },
      {
        source: '/openapi.json',
        destination: 'http://164.68.122.165/openapi.json', // Proxy openapi
      },
      {
        source: '/uploads/:path*',
        destination: 'http://164.68.122.165/uploads/:path*', // Proxy uploads
      },
    ]
  },
}

module.exports = nextConfig
