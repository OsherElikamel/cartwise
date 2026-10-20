import { ChevronRight, History } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import EmptyState from '../components/ui/EmptyState';
import Skeleton from '../components/ui/Skeleton';
import { useDocumentTitle } from '../hooks/useDocumentTitle';
import { useI18n } from '../i18n/LanguageContext';
import { getHistory } from '../services/lists';
import type { RunSummary } from '../types';
import { getErrorMessage } from '../utils/errors';

export default function HistoryPage() {
  const { t, tp, dateTime, price, chain } = useI18n();
  useDocumentTitle(t('title.history'));
  const [runs, setRuns] = useState<RunSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHistory().then(setRuns).catch((err) => setError(getErrorMessage(err, t)));
  }, [t]);

  return (
    <div className="space-y-5">
      <header className="pt-2">
        <h1 className="text-3xl font-extrabold tracking-tight">{t('history.title')}</h1>
        <p className="mt-1 text-sm text-app-text-secondary">{t('history.subtitle')}</p>
      </header>
      {error && <p role="alert" className="rounded-2xl bg-danger/10 px-4 py-3 text-sm text-danger">{error}</p>}
      {runs === null && !error && <div className="space-y-2">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-16" />)}</div>}
      {runs?.length === 0 && (
        <EmptyState icon={<History size={40} />} title={t('history.emptyTitle')}>
          {t('history.emptyBody')}
        </EmptyState>
      )}
      {runs && runs.length > 0 && (
        <ul className="divide-y divide-app-border overflow-hidden rounded-3xl border border-app-border bg-app-surface/80">
          {runs.map((run) => (
            <li key={run.id}>
              <Link to={`/history/${run.id}`} className="flex items-center gap-3 px-4 py-3 hover:bg-app-hover">
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold"><bdi>{run.list_name ?? t('history.quickCompare')}</bdi> <span className="font-normal text-app-text-secondary">· {tp('history.items', run.item_count)}</span></p>
                  <p className="text-xs text-app-text-secondary">{dateTime(run.created_at)} · {t('history.cheapestAt', { chain: chain(run.cheapest_chain) })}</p>
                </div>
                <div className="text-end">
                  <p className="font-mono text-sm font-bold">{price(run.cheapest_total)}</p>
                  {Number(run.savings) > 0 && <p className="font-mono text-xs text-success">{t('history.saved', { amount: price(run.savings) })}</p>}
                </div>
                <ChevronRight size={16} className="text-app-text-secondary rtl:rotate-180" aria-hidden />
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
