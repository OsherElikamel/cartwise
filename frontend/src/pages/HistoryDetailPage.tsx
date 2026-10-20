import { ArrowLeft } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import ResultsView from '../components/basket/ResultsView';
import Skeleton from '../components/ui/Skeleton';
import { useDocumentTitle } from '../hooks/useDocumentTitle';
import { useI18n } from '../i18n/LanguageContext';
import { getRun } from '../services/lists';
import type { RunDetail } from '../types';
import { getErrorMessage } from '../utils/errors';

export default function HistoryDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [run, setRun] = useState<RunDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { t, dateTime } = useI18n();
  const name = run?.list_name ?? t('history.quickCompare');
  useDocumentTitle(run ? `${name}, ${dateTime(run.created_at)}` : t('title.history'));

  useEffect(() => {
    if (!id) return;
    getRun(id).then(setRun).catch((err) => setError(getErrorMessage(err, t)));
  }, [id, t]);

  return (
    <div className="space-y-5">
      <Link to="/history" className="inline-flex items-center gap-1.5 text-sm font-medium text-app-text-secondary hover:text-app-text">
        <ArrowLeft size={16} className="rtl:rotate-180" aria-hidden /> {t('history.all')}
      </Link>
      {error && <p role="alert" className="rounded-2xl bg-danger/10 px-4 py-3 text-sm text-danger">{error}</p>}
      {!run && !error && <Skeleton className="h-64" />}
      {run && (
        <>
          <header>
            <h1 dir="auto" className="text-3xl font-extrabold tracking-tight">{name}</h1>
            <p className="text-sm text-app-text-secondary">{dateTime(run.created_at)} · {t('history.pricesThatDay')}</p>
          </header>
          <ResultsView result={run.result} editable={false} canSave={false} />
        </>
      )}
    </div>
  );
}
