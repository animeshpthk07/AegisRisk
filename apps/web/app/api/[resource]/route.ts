import { NextRequest, NextResponse } from 'next/server';
const reads = new Set(['health', 'ready', 'portfolio', 'facilities', 'explanation']);
async function forward(request: NextRequest, context: { params: Promise<{ resource: string }> }) {
  const { resource } = await context.params;
  if (!(request.method === 'GET' ? reads.has(resource) : resource === 'stress')) {
    return NextResponse.json({ detail: 'Not found' }, { status: 404 });
  }
  let body: string | undefined;
  if (request.method === 'POST') {
    body = await request.text();
    if (body.length > 4096) return NextResponse.json({ detail: 'Request too large' }, { status: 413 });
  }
  try {
    const response = await fetch(`${process.env.API_BASE_URL || 'http://127.0.0.1:8000'}/api/v1/${resource}${request.nextUrl.search}`, {
      method: request.method, headers: { 'Content-Type': 'application/json' }, body,
      cache: 'no-store', signal: AbortSignal.timeout(8000), redirect: 'error',
    });
    const payload = await response.json();
    return NextResponse.json(payload, { status: response.status, headers: { 'Cache-Control': 'no-store' } });
  } catch {
    return NextResponse.json({ detail: 'Backend unavailable. Start the API and check database readiness.' }, { status: 503 });
  }
}
export const GET = forward;
export const POST = forward;
