'use client';

import { createContext, useContext, useEffect, useRef, useState, type FormEvent, type ReactNode } from 'react';

// Deliberately memory-only: never put bearer credentials in URLs, cookies or storage.
let bearer = '';
let generation = 0;
const pending = new Set<AbortController>();
const LOCK_EVENT = 'aegisrisk:lock';
type Identity = { mode: 'local' | 'token'; subject: string; workspace: string; role: 'viewer' | 'analyst' };
const AccessContext = createContext<Identity | null>(null);
export function useAccess() { return useContext(AccessContext); }

function forgetCredential() {
  bearer = ''; generation += 1;
  for (const controller of pending) controller.abort();
  pending.clear();
}

export async function workbenchFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const url = new URL(path, window.location.origin);
  if (!path.startsWith('/api/') || url.origin !== window.location.origin || !url.pathname.startsWith('/api/')) {
    throw new Error('Workbench requests must stay on this site.');
  }
  const epoch = generation;
  const controller = new AbortController();
  pending.add(controller);
  const headers = new Headers(init.headers);
  headers.delete('Authorization');
  if (bearer) headers.set('Authorization', 'Bearer ' + bearer);
  try {
    const response = await window.fetch(path, { ...init, headers, credentials: 'omit', cache: 'no-store',
      redirect: 'error', signal: AbortSignal.any([controller.signal, AbortSignal.timeout(15000), ...(init.signal ? [init.signal] : [])]) });
    if (epoch !== generation) throw new DOMException('Workspace locked', 'AbortError');
    if (response.status === 401) window.dispatchEvent(new Event(LOCK_EVENT));
    return response;
  } finally { pending.delete(controller); }
}

async function identify(token: string, signal: AbortSignal): Promise<Identity | null> {
  const response = await window.fetch('/api/access', {
    headers: token ? { Authorization: 'Bearer ' + token } : {},
    credentials: 'omit', cache: 'no-store', redirect: 'error',
    signal: AbortSignal.any([signal, AbortSignal.timeout(10000)]),
  });
  if (response.status === 401) return null;
  if (!response.ok) throw new Error('Access service unavailable. Please retry.');
  const data = await response.json();
  if (!['local', 'token'].includes(data.mode) || !['viewer', 'analyst'].includes(data.role) ||
      typeof data.subject !== 'string' || typeof data.workspace !== 'string' ||
      (token && data.mode !== 'token') || (!token && data.mode !== 'local')) {
    throw new Error('Access service returned an invalid response.');
  }
  return data;
}

export default function AccessGate({ children }: { children: ReactNode }) {
  const [identity, setIdentity] = useState<Identity | null>(null);
  const [status, setStatus] = useState<'checking' | 'locked' | 'ready' | 'error'>('checking');
  const [credential, setCredential] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const request = useRef<AbortController | null>(null);
  const input = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const controller = new AbortController();
    request.current = controller;
    forgetCredential();
    void identify('', controller.signal).then(value => {
      if (controller.signal.aborted) return;
      setIdentity(value); setStatus(value ? 'ready' : 'locked');
    }).catch(() => {
      if (!controller.signal.aborted) { setStatus('error'); setMessage('Access service unavailable. Please retry.'); }
    });
    return () => { controller.abort(); request.current?.abort(); forgetCredential(); };
  }, [attempt]);

  useEffect(() => {
    function lock() {
      request.current?.abort(); forgetCredential(); setIdentity(null); setCredential('');
      setBusy(false); setMessage('Workbench locked. Enter a valid token to continue.'); setStatus('locked');
    }
    function leaving() { if (bearer) lock(); }
    window.addEventListener(LOCK_EVENT, lock);
    window.addEventListener('pagehide', leaving);
    return () => { window.removeEventListener(LOCK_EVENT, lock); window.removeEventListener('pagehide', leaving); };
  }, []);
  useEffect(() => { if (status === 'locked') input.current?.focus(); }, [status]);

  async function unlock(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!/^[A-Za-z0-9_-]{43}$/.test(credential) || busy) return;
    const candidate = credential;
    setCredential(''); setBusy(true); setMessage('');
    request.current?.abort();
    const controller = new AbortController(); request.current = controller;
    try {
      const value = await identify(candidate, controller.signal);
      if (controller.signal.aborted) return;
      if (!value) { setMessage('Token is invalid, expired or revoked.'); return; }
      forgetCredential(); bearer = candidate; setIdentity(value); setStatus('ready');
    } catch {
      if (!controller.signal.aborted) setMessage('Access service unavailable. Please retry.');
    } finally { if (!controller.signal.aborted) setBusy(false); }
  }

  if (status === 'ready' && identity) return <AccessContext.Provider value={identity}>
    {identity.mode === 'token' && <aside className="access-session" aria-label="Workspace access">
      <span>{identity.role === 'viewer' ? 'Read-only workspace' : 'Analyst workspace'} · Private access</span>
      <button type="button" onClick={() => window.dispatchEvent(new Event(LOCK_EVENT))}>Lock workbench</button>
    </aside>}
    {children}
  </AccessContext.Provider>;
  return <main className="access-screen"><section className="panel" aria-labelledby="access-heading">
    <p className="eyebrow">AEGISRISK / WORKSPACE ACCESS</p>
    <h1 id="access-heading">{status === 'locked' ? 'Unlock your workspace' : 'Connecting to AegisRisk'}</h1>
    <p>Fictional-data research workbench. Do not upload real customer information.</p>
    {status === 'checking' && <p role="status">Checking workspace access…</p>}
    {message && <p role={status === 'error' || message.includes('invalid') ? 'alert' : 'status'}>{message}</p>}
    {status === 'error' && <button type="button" onClick={() => { setStatus('checking'); setMessage(''); setAttempt(value => value + 1); }}>Retry connection</button>}
    {status === 'locked' && <form onSubmit={unlock}>
      <label htmlFor="access-token">Access token</label>
      <input ref={input} id="access-token" type="password" value={credential} required minLength={43} maxLength={43}
        pattern="[A-Za-z0-9_-]{43}" autoComplete="off" spellCheck={false} autoCapitalize="none"
        aria-describedby="access-help" disabled={busy} onChange={event => setCredential(event.target.value)}/>
      <p id="access-help">Use the token supplied by your workspace administrator. It stays in memory for this tab and is cleared on refresh or lock.</p>
      <button type="submit" disabled={busy || !/^[A-Za-z0-9_-]{43}$/.test(credential)}>{busy ? 'Checking token…' : 'Unlock workspace'}</button>
      <p className="muted">Locking clears this screen; an administrator must revoke a lost token.</p>
    </form>}
  </section></main>;
}
