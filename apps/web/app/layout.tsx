import type { Metadata } from 'next';
import './globals.css';
import AccessGate from './access';
export const metadata: Metadata = { title: 'AegisRisk | Credit intelligence', description: 'Transparent credit-risk analytics using fictional data. Educational demonstration only.' };
export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body><AccessGate>{children}</AccessGate></body></html>;
}
