import { NextRequest, NextResponse } from 'next/server';

const reads = new Set(['health', 'ready', 'portfolio', 'facilities', 'explanation', 'saved-portfolios']);
const writes = new Set(['stress', 'import-preview', 'saved-portfolios']);
const safeHeaders = { 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff' };
function error(detail: string, status: number) {
  return NextResponse.json({ detail }, { status, headers: safeHeaders });
}

async function forward(request: NextRequest, context: { params: Promise<{ resource: string }> }) {
  const { resource } = await context.params;
  if (!(request.method === 'GET' ? reads.has(resource) : writes.has(resource))) {
    return error('Not found', 404);
  }
  const saving = resource === 'saved-portfolios';
  const csv = resource === 'import-preview' || saving;
  const headers: Record<string, string> = { 'Content-Type': csv ? 'text/csv' : 'application/json' };
  let body: ArrayBuffer | undefined;
  if (request.method === 'POST') {
    if (csv) {
      if (request.headers.get('x-aegisrisk-synthetic') !== 'true') {
        return error('Confirm synthetic data only before previewing', 400);
      }
      if (request.headers.get('content-type')?.split(';')[0].trim().toLowerCase() !== 'text/csv') {
        return error('Send a UTF-8 CSV file', 415);
      }
      headers['X-AegisRisk-Synthetic'] = 'true';
      if (saving) {
        if (request.headers.get('x-aegisrisk-reviewed') !== 'true') {
          return error('Review the preview and confirm saving', 400);
        }
        const digest = request.headers.get('x-aegisrisk-preview-digest') || '';
        if (!/^[a-f0-9]{64}$/.test(digest)) return error('Validate the file again', 409);
        headers['X-AegisRisk-Reviewed'] = 'true';
        headers['X-AegisRisk-Preview-Digest'] = digest;
      }
    }
    const limit = csv ? 262144 : 4096;
    const reader = request.body?.getReader();
    const chunks: Uint8Array[] = [];
    let size = 0;
    try {
      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          size += value.byteLength;
          if (size > limit) {
            void reader.cancel().catch(() => {});
            return error('Request exceeds the upload size limit', 413);
          }
          chunks.push(value);
        }
      }
    } catch {
      return error('Could not read the uploaded file', 400);
    } finally {
      reader?.releaseLock();
    }
    const bytes = new Uint8Array(size);
    let offset = 0;
    for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
    body = bytes.buffer;
  }
  try {
    const response = await fetch(
      `${process.env.API_BASE_URL || 'http://127.0.0.1:8000'}/api/v1/${resource}${request.nextUrl.search}`,
      { method: request.method, headers, body, cache: 'no-store',
        signal: AbortSignal.timeout(8000), redirect: 'error' },
    );
    const payload = await response.json();
    return NextResponse.json(payload, { status: response.status, headers: safeHeaders });
  } catch {
    return error('Backend unavailable. Start the API and check database readiness.', 503);
  }
}
export const GET = forward;
export const POST = forward;
