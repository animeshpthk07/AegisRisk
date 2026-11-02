import type { Metadata } from 'next';
import { connection } from 'next/server';
import './globals.css';
import AccessGate from './access';
export const metadata: Metadata = { title: 'AegisRisk | Credit intelligence', description: 'Transparent credit-risk analytics using fictional data. Educational demonstration only.' };
export default async function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  // Request-time rendering lets Next.js apply this response's CSP nonce.
  await connection();
  return <html lang="en"><body><AccessGate>{children}</AccessGate></body></html>;
}
