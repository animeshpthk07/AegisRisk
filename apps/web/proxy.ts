import { NextRequest, NextResponse } from 'next/server';

export function proxy(request: NextRequest) {
  // Fresh 256-bit randomness per response; never trust a caller-supplied nonce.
  const nonce = Buffer.from(crypto.getRandomValues(new Uint8Array(32))).toString('base64');
  const development = process.env.NODE_ENV === 'development';
  const policy = [
    "default-src 'none'",
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${development ? " 'unsafe-eval'" : ''}`,
    "script-src-attr 'none'",
    `style-src 'self' ${development ? "'unsafe-inline'" : "'nonce-" + nonce + "'"}`,
    // Recharts/React position charts with style attributes. This does not allow scripts.
    "style-src-attr 'unsafe-inline'",
    `connect-src 'self'${development ? ' ws: wss:' : ''}`,
    "img-src 'self' data: blob:",
    "font-src 'self'",
    "object-src 'none'",
    "frame-src 'none'",
    "worker-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
  ].join('; ');
  const headers = new Headers(request.headers);
  headers.set('x-nonce', nonce);
  headers.set('Content-Security-Policy', policy);
  const response = NextResponse.next({ request: { headers } });
  response.headers.set('Content-Security-Policy', policy);
  // Nonced documents must not be shared or reused by an intermediary cache.
  response.headers.set('Cache-Control', 'private, no-store');
  return response;
}

export const config = {
  // Include API errors, unknown pages and prefetch headers. Only static assets skip it.
  matcher: ['/((?!_next/static/|_next/image(?:/|$)|favicon[.]ico$).*)'],
};
