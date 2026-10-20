import { useI18n } from '../../i18n/LanguageContext';
import type { StoreBasket } from '../../types';

interface StoreRankingProps {
  stores: StoreBasket[];
  selectedId: string;
  onSelect: (storeId: string) => void;
}

export default function StoreRanking({ stores, selectedId, onSelect }: StoreRankingProps) {
  const { t, tp, price, chain } = useI18n();
  const totals = stores.map((s) => Number(s.shared_total));
  const cheapest = Math.min(...totals);
  const highest = Math.max(...totals) || 1;

  return (
    <ol className="flex flex-col gap-2" aria-label={t('results.rankingAria')}>
      {stores.map((store, i) => {
        const total = totals[i];
        const selected = store.store_id === selectedId;
        return (
          <li key={store.store_id}>
            <button
              type="button"
              onClick={() => onSelect(store.store_id)}
              aria-pressed={selected}
              className={`w-full rounded-2xl border p-3.5 text-start transition-colors ${
                selected ? 'border-accent bg-app-surface' : 'border-app-border bg-app-surface/50 hover:bg-app-surface'
              }`}
            >
              <div className="flex items-baseline gap-2">
                <span className="font-mono text-xs text-app-text-secondary">{i + 1}</span>
                <span className="font-semibold">{chain(store.chain_slug)}</span>
                <span dir="auto" className="min-w-0 flex-1 truncate text-xs text-app-text-secondary">{store.store_name}</span>
                <span className="font-mono font-bold">{price(total)}</span>
              </div>
              <div className="mt-2.5 flex items-center gap-3">
                <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-app-elevated">
                  <div
                    className={`h-full rounded-full ${i === 0 ? 'bg-linear-to-r from-brand-from to-accent rtl:bg-linear-to-l' : 'bg-app-text-secondary/40'}`}
                    style={{ width: `${Math.max(8, (total / highest) * 100)}%` }}
                  />
                </div>
                <span className="w-20 text-end font-mono text-xs text-app-text-secondary">
                  {i === 0 ? t('results.cheapest') : `+${price(total - cheapest)}`}
                </span>
              </div>
              {store.missing.length > 0 && (
                <p className="mt-1.5 text-xs text-warning">{tp('results.missing', store.missing.length)}</p>
              )}
            </button>
          </li>
        );
      })}
    </ol>
  );
}
