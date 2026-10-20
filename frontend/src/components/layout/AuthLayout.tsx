import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import BrandMark from '../ui/BrandMark';

export default function AuthLayout({ title, subtitle, children, footer }: { title: string; subtitle: string; children: ReactNode; footer: ReactNode }) {
  return (
    <div className="relative mx-auto flex max-w-sm flex-col items-center py-6">
      <div aria-hidden className="pointer-events-none absolute -top-10 left-1/4 -z-10 h-64 w-64 rounded-full bg-accent opacity-[0.06] blur-3xl" />
      <div aria-hidden className="pointer-events-none absolute bottom-0 right-0 -z-10 h-56 w-56 rounded-full bg-deal opacity-[0.08] blur-3xl" />
      <Link to="/" aria-label="CartWise home"><BrandMark size="lg" /></Link>
      <h1 className="mt-4 text-2xl font-bold tracking-tight">{title}</h1>
      <p className="mt-1 text-center text-sm text-app-text-secondary">{subtitle}</p>
      <div className="mt-6 w-full rounded-2xl border border-app-border bg-app-surface p-5">{children}</div>
      <div className="mt-4 text-sm text-app-text-secondary">{footer}</div>
    </div>
  );
}
