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
        destination: 'https://toluwanimi465-pharmgpt-backend.hf.space/api/:path*', // Proxy to HF Space
      },
      {
        source: '/docs',
        destination: 'https://toluwanimi465-pharmgpt-backend.hf.space/docs', // Proxy docs
      },
      {
        source: '/openapi.json',
        destination: 'https://toluwanimi465-pharmgpt-backend.hf.space/openapi.json', // Proxy openapi
      },
    ]
  },
}

module.exports = nextConfig
