import { AlertTriangle, Info, Sparkles } from 'lucide-react';
import { useState } from 'react';
import type { Alternative, BasketComparison, BasketLine, StoreBasket } from '../../types';
import { formatPrice } from '../../utils/format';
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
  const [selectedId, setSelectedId] = useState(result.stores[0]?.store_id ?? '');
  const selected = result.stores.find((s) => s.store_id === selectedId) ?? result.stores[0];
  const cheapest = result.stores[0];
  const toCheck = result.stores.reduce((n, s) => n + s.lines.filter((l) => l.confidence === 'low').length, 0);
  const allItems = result.items.length;
  const shared = result.shared_items.length;

  if (!cheapest) return null;

  return (
    <div className="animate-fade-in space-y-5">
      <section className="rounded-2xl border border-app-border bg-app-surface p-5">
        <p className="text-sm text-app-text-secondary">Cheapest basket</p>
        <p className="mt-1 text-2xl font-bold tracking-tight">
          <span className="marker">{cheapest.chain_name}</span>{' '}
          <span className="font-mono">{formatPrice(cheapest.shared_total)}</span>
        </p>
        {Number(result.savings_vs_most_expensive) > 0 && (
          <p className="mt-1 text-sm">
            <span className="font-semibold text-success">{formatPrice(result.savings_vs_most_expensive)} less</span>{' '}
            than the most expensive store
          </p>
        )}
        <p className="mt-3 flex items-start gap-1.5 text-xs text-app-text-secondary">
          <Info size={14} className="mt-px shrink-0" aria-hidden />
          {shared === allItems
            ? `All ${allItems} items were found at every store.`
            : `Ranked on the ${shared} of ${allItems} items every store has, so a store can't look cheaper by missing something.`}
        </p>
        {result.remembered_matches > 0 && (
          <p className="mt-1 flex items-center gap-1.5 text-xs text-app-text-secondary">
            <Sparkles size={14} aria-hidden />
            {result.remembered_matches} product pick{result.remembered_matches === 1 ? '' : 's'} came from your saved choices.
          </p>
        )}
      </section>

      {editable && toCheck > 0 && (
        <p role="status" className="flex items-start gap-2 rounded-2xl bg-warning/10 px-4 py-3 text-sm text-warning">
          <AlertTriangle size={16} className="mt-0.5 shrink-0" aria-hidden />
          {toCheck} pick{toCheck === 1 ? '' : 's'} need a quick check. The AI wasn't sure, so it's asking you instead of guessing.
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
