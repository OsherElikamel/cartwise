import type { StoreBasket } from '../../types';
import { formatPrice } from '../../utils/format';

interface StoreRankingProps {
  stores: StoreBasket[];
  selectedId: string;
  onSelect: (storeId: string) => void;
}

export default function StoreRanking({ stores, selectedId, onSelect }: StoreRankingProps) {
  const totals = stores.map((s) => Number(s.shared_total));
  const cheapest = Math.min(...totals);
  const highest = Math.max(...totals) || 1;

  return (
    <ol className="flex flex-col gap-2" aria-label="Stores, cheapest first">
      {stores.map((store, i) => {
        const total = totals[i];
        const diff = total - cheapest;
        const selected = store.store_id === selectedId;
        return (
          <li key={store.store_id}>
            <button
              type="button"
              onClick={() => onSelect(store.store_id)}
              aria-pressed={selected}
              className={`w-full rounded-2xl border p-3 text-left transition-colors ${
                selected ? 'border-accent bg-app-surface' : 'border-app-border bg-app-surface/60 hover:bg-app-surface'
              }`}
            >
              <div className="flex items-baseline gap-2">
                <span className="font-mono text-xs text-app-text-secondary">{i + 1}</span>
                <span className="font-semibold">{store.chain_name}</span>
                <span dir="auto" className="min-w-0 flex-1 truncate text-xs text-app-text-secondary">{store.store_name}</span>
                <span className="font-mono font-bold">{formatPrice(total)}</span>
              </div>
              <div className="mt-2 flex items-center gap-3">
                <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-app-elevated">
                  <div
                    className={`h-full rounded-full ${i === 0 ? 'bg-accent' : 'bg-app-text-secondary/40'}`}
                    style={{ width: `${Math.max(8, (total / highest) * 100)}%` }}
                  />
                </div>
                <span className="w-20 text-right font-mono text-xs text-app-text-secondary">
                  {i === 0 ? 'cheapest' : `+${formatPrice(diff)}`}
                </span>
              </div>
              {store.missing.length > 0 && (
                <p className="mt-1.5 text-xs text-warning">
                  {store.missing.length} item{store.missing.length > 1 ? 's' : ''} not found here
                </p>
              )}
            </button>
          </li>
        );
      })}
    </ol>
  );
}
