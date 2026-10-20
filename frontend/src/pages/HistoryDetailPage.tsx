import { ArrowLeft } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import ResultsView from '../components/basket/ResultsView';
import Skeleton from '../components/ui/Skeleton';
import { useDocumentTitle } from '../hooks/useDocumentTitle';
import { getRun } from '../services/lists';
import type { RunDetail } from '../types';
import { getErrorMessage } from '../utils/errors';
import { formatDateTime } from '../utils/format';

export default function HistoryDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [run, setRun] = useState<RunDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  useDocumentTitle(run ? `${run.list_name ?? 'Quick compare'}, ${formatDateTime(run.created_at)}` : 'History');

  useEffect(() => {
    if (!id) return;
    getRun(id).then(setRun).catch((err) => setError(getErrorMessage(err)));
  }, [id]);

  return (
    <div className="space-y-5">
      <Link to="/history" className="inline-flex items-center gap-1.5 text-sm font-medium text-app-text-secondary hover:text-app-text">
        <ArrowLeft size={16} aria-hidden /> All comparisons
      </Link>
      {error && <p role="alert" className="rounded-2xl bg-danger/10 px-4 py-3 text-sm text-danger">{error}</p>}
      {!run && !error && <Skeleton className="h-64" />}
      {run && (
        <>
          <header>
            <h1 className="text-2xl font-bold tracking-tight">{run.list_name ?? 'Quick compare'}</h1>
            <p className="text-sm text-app-text-secondary">{formatDateTime(run.created_at)} · prices as they were that day</p>
          </header>
          <ResultsView result={run.result} editable={false} canSave={false} />
        </>
      )}
    </div>
  );
}
