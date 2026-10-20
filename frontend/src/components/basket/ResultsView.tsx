import { AlertTriangle, Clock, Info, Sparkles } from 'lucide-react';
import { useState } from 'react';
import { useI18n } from '../../i18n/LanguageContext';
import type { Alternative, BasketComparison, BasketLine, StoreBasket } from '../../types';
import StoreRanking from './StoreRanking';
import StoreReceipt from './StoreReceipt';

interface ResultsViewProps {
  result: BasketComparison;
  editable: boolean;
  canSave: boolean;
  busyLine?: string | null;
  onConfirm?: (store: StoreBasket, line: BasketLine) => void;
  onSwap?: (store: StoreBasket, line: BasketLine, alt: Alternative) => void;
}

export default function ResultsView({ result, editable, canSave, busyLine = null, onConfirm, onSwap }: ResultsViewProps) {
  const { t, tp, price, chain, dateTime } = useI18n();
  const [selectedId, setSelectedId] = useState(result.stores[0]?.store_id ?? '');
  const selected = result.stores.find((s) => s.store_id === selectedId) ?? result.stores[0];
  const cheapest = result.stores[0];
  const toCheck = result.stores.reduce((n, s) => n + s.lines.filter((l) => l.confidence === 'low').length, 0);
  const total = result.items.length;
  const shared = result.shared_items.length;
  // The oldest branch's load time: every price shown is at least this fresh.
  const loadedTimes = result.stores.map((s) => s.prices_updated_at).filter((v): v is string => Boolean(v)).sort();
  const pricesFrom = loadedTimes[0];

  if (!cheapest) return null;

  return (
    <div className="animate-fade-in space-y-5">
      <section className="rounded-3xl border border-app-border bg-app-surface/80 p-6">
        <p className="text-sm text-app-text-secondary">{t('results.cheapestBasket')}</p>
        <p className="mt-1 flex flex-wrap items-baseline gap-x-3 text-3xl font-extrabold tracking-tight">
          <span className="marker">{chain(cheapest.chain_slug)}</span>
          <span className="font-mono text-2xl">{price(cheapest.shared_total)}</span>
        </p>
        {Number(result.savings_vs_most_expensive) > 0 && (
          <p className="mt-2 text-sm">
            <span className="font-semibold text-success">{t('results.less', { amount: price(result.savings_vs_most_expensive) })}</span>{' '}
            {t('results.thanMostExpensive')}
          </p>
        )}
        <p className="mt-3 flex items-start gap-1.5 text-xs text-app-text-secondary">
          <Info size={14} className="mt-px shrink-0" aria-hidden />
          {shared === total ? t('results.allFound', { count: total }) : t('results.rankedOnShared', { shared, total })}
        </p>
        {pricesFrom && (
          <p className="mt-1 flex items-center gap-1.5 text-xs text-app-text-secondary">
            <Clock size={14} aria-hidden />
            {t('results.pricesFrom', { when: dateTime(pricesFrom) })}
          </p>
        )}
        {result.remembered_matches > 0 && (
          <p className="mt-1 flex items-center gap-1.5 text-xs text-app-text-secondary">
            <Sparkles size={14} aria-hidden />
            {tp('results.fromSaved', result.remembered_matches)}
          </p>
        )}
      </section>

      {result.ai_available === false && (
        <p role="status" className="flex items-start gap-2 rounded-2xl bg-app-elevated px-4 py-3 text-sm">
          <Info size={16} className="mt-0.5 shrink-0 text-accent" aria-hidden />
          {t('results.aiResting')}
        </p>
      )}

      {editable && toCheck > 0 && (
        <p role="status" className="flex items-start gap-2 rounded-2xl bg-warning/10 px-4 py-3 text-sm text-warning">
          <AlertTriangle size={16} className="mt-0.5 shrink-0" aria-hidden />
          {tp('results.needCheck', toCheck)}
        </p>
      )}

      <div className="grid gap-5 md:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
        <StoreRanking stores={result.stores} selectedId={selected.store_id} onSelect={setSelectedId} />
        <StoreReceipt
          store={selected}
          items={result.items}
          sharedItems={result.shared_items}
          editable={editable}
          canSave={canSave}
          busyLine={busyLine}
          onConfirm={onConfirm ? (line) => onConfirm(selected, line) : undefined}
          onSwap={onSwap ? (line, alt) => onSwap(selected, line, alt) : undefined}
        />
      </div>
    </div>
  );
}
