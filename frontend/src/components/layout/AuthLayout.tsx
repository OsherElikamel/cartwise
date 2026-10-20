import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { useI18n } from '../../i18n/LanguageContext';
import BrandMark from '../ui/BrandMark';

export default function AuthLayout({ title, subtitle, children, footer }: { title: string; subtitle: string; children: ReactNode; footer: ReactNode }) {
  const { t } = useI18n();
  return (
    <div className="mx-auto flex max-w-sm flex-col items-center py-6">
      <Link to="/" aria-label={t('nav.home')}><BrandMark size="lg" /></Link>
      <h1 className="mt-5 text-3xl font-extrabold tracking-tight">{title}</h1>
      <p className="mt-2 text-center text-sm text-app-text-secondary">{subtitle}</p>
      <div className="mt-6 w-full rounded-3xl border border-app-border bg-app-surface/70 p-6">{children}</div>
      <div className="mt-4 text-sm text-app-text-secondary">{footer}</div>
    </div>
  );
}
