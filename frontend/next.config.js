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
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'https://sep-quarterly-newark-swim.trycloudflare.com';
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
