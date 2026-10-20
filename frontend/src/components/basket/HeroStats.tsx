import { useI18n } from '../../i18n/LanguageContext';
import type { Chain } from '../../types';

/** Real numbers only: chains and branches come from the API. */
export default function HeroStats({ chains }: { chains: Chain[] }) {
  const { t } = useI18n();
  const branches = chains.reduce((n, c) => n + c.store_count, 0);
  const stats = [
    { value: String(chains.length), label: t('stats.chains') },
    { value: branches.toLocaleString(), label: t('stats.branches') },
    { value: t('stats.daily'), label: t('stats.dailyLabel') },
  ];
  return (
    <dl className="mx-auto flex max-w-xl items-center justify-center divide-x divide-app-border rtl:divide-x-reverse">
      {stats.map((s) => (
        <div key={s.label} className="flex flex-col items-center gap-1 px-3 sm:flex-row sm:gap-2.5 sm:px-6">
          <dt className="sr-only">{s.label}</dt>
          <dd className="font-mono text-2xl font-bold sm:text-3xl">{s.value}</dd>
          <dd aria-hidden className="max-w-24 text-center text-xs leading-tight text-app-text-secondary sm:max-w-20 sm:text-start">{s.label}</dd>
        </div>
      ))}
    </dl>
  );
}
