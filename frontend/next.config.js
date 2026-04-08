/** @type {import('next').NextConfig} */
const normalizeApiBaseUrl = (value) =>
  (value || 'http://localhost:8000')
    .replace(/\/+$/, '')
    .replace(/\/api\/v1$/, '')
    .replace(/\/api$/, '')

const apiBaseUrl = normalizeApiBaseUrl(process.env.NEXT_PUBLIC_API_URL)

const nextConfig = {
  output: 'standalone',
  env: {
    NEXT_PUBLIC_API_URL: apiBaseUrl,
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${apiBaseUrl}/api/:path*`,
      },
    ]
  },
}

module.exports = nextConfig
