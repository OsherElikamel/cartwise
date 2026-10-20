import { ChevronRight, History } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import EmptyState from '../components/ui/EmptyState';
import Skeleton from '../components/ui/Skeleton';
import { useDocumentTitle } from '../hooks/useDocumentTitle';
import { getHistory } from '../services/lists';
import type { RunSummary } from '../types';
import { getErrorMessage } from '../utils/errors';
import { formatDateTime, formatPrice } from '../utils/format';

export default function HistoryPage() {
  useDocumentTitle('History');
  const [runs, setRuns] = useState<RunSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHistory().then(setRuns).catch((err) => setError(getErrorMessage(err)));
  }, []);

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-2xl font-bold tracking-tight">History</h1>
        <p className="mt-1 text-sm text-app-text-secondary">Every comparison you've run, with the prices of that day.</p>
      </header>
      {error && <p role="alert" className="rounded-2xl bg-danger/10 px-4 py-3 text-sm text-danger">{error}</p>}
      {runs === null && !error && <div className="space-y-2">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-16" />)}</div>}
      {runs?.length === 0 && (
        <EmptyState icon={<History size={40} />} title="Nothing here yet">
          Your comparisons will show up here, so you can see how prices change week to week.
        </EmptyState>
      )}
      {runs && runs.length > 0 && (
        <ul className="divide-y divide-app-border rounded-2xl border border-app-border bg-app-surface">
          {runs.map((run) => (
            <li key={run.id}>
              <Link to={`/history/${run.id}`} className="flex items-center gap-3 px-4 py-3 hover:bg-app-hover">
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold">{run.list_name ?? 'Quick compare'} <span className="font-normal text-app-text-secondary">· {run.item_count} items</span></p>
                  <p className="text-xs text-app-text-secondary">{formatDateTime(run.created_at)} · cheapest at {run.cheapest_chain}</p>
                </div>
                <div className="text-right">
                  <p className="font-mono text-sm font-bold">{formatPrice(run.cheapest_total)}</p>
                  {Number(run.savings) > 0 && <p className="font-mono text-xs text-success">saved {formatPrice(run.savings)}</p>}
                </div>
                <ChevronRight size={16} className="text-app-text-secondary" aria-hidden />
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
