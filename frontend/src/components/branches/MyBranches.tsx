import { Loader2, MapPin, X } from 'lucide-react';
import type { Chain, Store } from '../../types';

interface MyBranchesProps {
  chains: Chain[];
  myStores: Store[];
  removingId: string | null;
  onRemove: (store: Store) => void;
}

export default function MyBranches({ chains, myStores, removingId, onRemove }: MyBranchesProps) {
  return (
    <ul className="grid gap-3 sm:grid-cols-2">
      {chains.map((chain) => {
        const store = myStores.find((s) => s.chain_slug === chain.slug);
        return (
          <li key={chain.slug} className={`rounded-2xl border p-4 ${store ? 'border-app-border bg-app-surface' : 'border-dashed border-app-border'}`}>
            <div className="flex items-start gap-2">
              <div className="min-w-0 flex-1">
                <p className="font-semibold">{chain.name} <span dir="rtl" className="text-sm font-normal text-app-text-secondary">{chain.name_he}</span></p>
                {store ? (
                  <>
                    <p dir="auto" className="mt-1 truncate text-sm">{store.name}</p>
                    {store.address && <p dir="auto" className="truncate text-xs text-app-text-secondary">{store.address}</p>}
                    {!store.is_ready && (
                      <p className="mt-2 flex items-center gap-1.5 text-xs text-warning">
                        <Loader2 size={12} className="animate-spin" aria-hidden /> Loading today's prices…
                      </p>
                    )}
                  </>
                ) : (
                  <p className="mt-1 flex items-center gap-1.5 text-sm text-app-text-secondary">
                    <MapPin size={14} aria-hidden /> Not chosen. Search below.
                  </p>
                )}
              </div>
              {store && (
                <button
                  type="button"
                  onClick={() => onRemove(store)}
                  disabled={removingId === store.id}
                  aria-label={`Remove ${chain.name} branch ${store.name}`}
                  className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-app-text-secondary hover:bg-app-hover hover:text-app-text disabled:opacity-50"
                >
                  <X size={16} />
                </button>
              )}
            </div>
          </li>
        );
      })}
    </ul>
  );
}
