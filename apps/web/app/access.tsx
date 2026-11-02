'use client';

import { createContext, useContext, useEffect, useRef, useState, type FormEvent, type ReactNode } from 'react';

// Deliberately memory-only: never put bearer credentials in URLs, cookies or storage.
let bearer = '';
let generation = 0;
const pending = new Set<AbortController>();
const LOCK_EVENT = 'aegisrisk:lock';
const IDLE_TIMEOUT_MS = 15 * 60 * 1000;
const IDLE_WARNING_MS = 60 * 1000;
let checkInactivity: (() => boolean) | null = null;
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
  if (checkInactivity?.()) throw new DOMException('Workspace locked', 'AbortError');
  const epoch = generation;
  const controller = new AbortController();
  pending.add(controller);
  const headers = new Headers(init.headers);
  headers.delete('Authorization');
  if (bearer) headers.set('Authorization', 'Bearer ' + bearer);
  try {
    const response = await window.fetch(path, { ...init, headers, credentials: 'omit', cache: 'no-store',
      redirect: 'error', signal: AbortSignal.any([controller.signal, AbortSignal.timeout(15000), ...(init.signal ? [init.signal] : [])]) });
    if (checkInactivity?.() || epoch !== generation) throw new DOMException('Workspace locked', 'AbortError');
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
  const [idleWarning, setIdleWarning] = useState(false);
  const extendSession = useRef<(() => void) | null>(null);
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
    function lock(event?: Event) {
      request.current?.abort(); forgetCredential(); setIdentity(null); setCredential('');
      setBusy(false); setIdleWarning(false);
      setMessage(event instanceof CustomEvent && event.detail === 'idle'
        ? 'Workbench locked after 15 minutes of inactivity. Enter your token to continue.'
        : 'Workbench locked. Enter a valid token to continue.');
      setStatus('locked');
    }
    function leaving() { if (bearer) lock(); }
    window.addEventListener(LOCK_EVENT, lock);
    window.addEventListener('pagehide', leaving);
    return () => { window.removeEventListener(LOCK_EVENT, lock); window.removeEventListener('pagehide', leaving); };
  }, []);
  useEffect(() => { if (status === 'locked') input.current?.focus(); }, [status]);

  useEffect(() => {
    if (status !== 'ready' || identity?.mode !== 'token') return;
    let lastWall = Date.now();
    let lastMonotonic = performance.now();
    let finished = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    function check() {
      if (finished) return true;
      // Wall time covers sleeping tabs; monotonic time prevents clock rollback extending access.
      const elapsed = Math.max(Date.now() - lastWall, performance.now() - lastMonotonic);
      if (timer !== undefined) clearTimeout(timer);
      if (elapsed >= IDLE_TIMEOUT_MS) {
        finished = true;
        window.dispatchEvent(new CustomEvent(LOCK_EVENT, { detail: 'idle' }));
        return true;
      }
      const warning = elapsed >= IDLE_TIMEOUT_MS - IDLE_WARNING_MS;
      setIdleWarning(warning);
      timer = setTimeout(check, Math.max(1,
        (warning ? IDLE_TIMEOUT_MS : IDLE_TIMEOUT_MS - IDLE_WARNING_MS) - elapsed));
      return false;
    }
    function extend() {
      // An event arriving after suspension must not revive an expired session.
      if (check() || document.visibilityState === 'hidden') return;
      lastWall = Date.now(); lastMonotonic = performance.now(); check();
    }
    function activity(event: Event) { if (event.isTrusted) extend(); }
    const events = ['pointerdown', 'keydown', 'wheel'];
    checkInactivity = check; extendSession.current = extend;
    for (const event of events) document.addEventListener(event, activity, { capture: true, passive: true });
    document.addEventListener('visibilitychange', check);
    window.addEventListener('focus', check);
    window.addEventListener('pageshow', check);
    check();
    return () => {
      finished = true;
      if (timer !== undefined) clearTimeout(timer);
      if (checkInactivity === check) checkInactivity = null;
      extendSession.current = null;
      for (const event of events) document.removeEventListener(event, activity, true);
      document.removeEventListener('visibilitychange', check);
      window.removeEventListener('focus', check);
      window.removeEventListener('pageshow', check);
    };
  }, [status, identity]);

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
      <span>{identity.role === 'viewer' ? 'Read-only workspace' : 'Analyst workspace'} · Locks after 15 minutes idle</span>
      {idleWarning && <span role="status">Locks in under a minute. Unsaved work will be cleared.</span>}
      {idleWarning && <button type="button" onClick={() => extendSession.current?.()}>Stay unlocked</button>}
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
      <p id="access-help">Use the token supplied by your workspace administrator. It stays in memory for this tab and is cleared on refresh or lock. The workbench locks after 15 minutes of inactivity, with a one-minute warning.</p>
      <button type="submit" disabled={busy || !/^[A-Za-z0-9_-]{43}$/.test(credential)}>{busy ? 'Checking token…' : 'Unlock workspace'}</button>
      <p className="muted">Locking clears this screen; an administrator must revoke a lost token.</p>
    </form>}
  </section></main>;
}
