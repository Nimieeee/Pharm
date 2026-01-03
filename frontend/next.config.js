/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'https://35-181-4-139.sslip.io',
  },
  experimental: {
    // Optimize package imports
    optimizePackageImports: ['lucide-react', 'framer-motion'],
  },
  async rewrites() {
    // Force HTTPS for the default fallback
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'https://35-181-4-139.sslip.io';
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`, // Proxy to Backend via Cloudflare Tunnel
      },
      {
        source: '/docs',
        destination: `${backendUrl}/docs`, // Proxy docs
      },
      {
        source: '/openapi.json',
        destination: `${backendUrl}/openapi.json`, // Proxy openapi
      },
      {
        source: '/uploads/:path*',
        destination: `${backendUrl}/uploads/:path*`, // Proxy uploads
      },
    ]
  },
}

module.exports = nextConfig

