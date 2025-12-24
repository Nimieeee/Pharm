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
        destination: 'https://pharmgpt.164.68.122.165.sslip.io/api/:path*', // Proxy to SSL Backend
      },
      {
        source: '/docs',
        destination: 'https://pharmgpt.164.68.122.165.sslip.io/docs', // Proxy docs
      },
      {
        source: '/openapi.json',
        destination: 'https://pharmgpt.164.68.122.165.sslip.io/openapi.json', // Proxy openapi
      },
      {
        source: '/uploads/:path*',
        destination: 'https://pharmgpt.164.68.122.165.sslip.io/uploads/:path*', // Proxy uploads
      },
    ]
  },
}

module.exports = nextConfig
