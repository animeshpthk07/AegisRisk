import type { NextConfig } from 'next';

const config: NextConfig = {
  output: 'standalone',
  poweredByHeader: false,
  async headers() {
    return [{
      source: '/:path*',
      headers: [
        { key: 'X-Content-Type-Options', value: 'nosniff' },
        { key: 'Referrer-Policy', value: 'no-referrer' },
        { key: 'X-Frame-Options', value: 'DENY' },
        {
          key: 'Permissions-Policy',
          value: 'camera=(), microphone=(), geolocation=(), payment=()',
        },
        {
          key: 'Content-Security-Policy',
          // Baseline restrictions; script/style nonce policy is a separate task.
          value: "base-uri 'self'; object-src 'none'; frame-ancestors 'none'; form-action 'self'",
        },
      ],
    }];
  },
};

export default config;
