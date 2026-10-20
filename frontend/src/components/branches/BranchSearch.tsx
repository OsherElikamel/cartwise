import { Check, Search } from 'lucide-react';
import { useEffect, useState } from 'react';
import { searchStores } from '../../services/catalog';
import type { Chain, Store } from '../../types';
import { getErrorMessage } from '../../utils/errors';
import Button from '../ui/Button';
import Skeleton from '../ui/Skeleton';

interface BranchSearchProps {
  chains: Chain[];
  followedIds: Set<string>;
  followingId: string | null;
  onFollow: (store: Store) => void;
}

export default function BranchSearch({ chains, followedIds, followingId, onFollow }: BranchSearchProps) {
  const [query, setQuery] = useState('');
  const [chain, setChain] = useState<string>('');
  const [results, setResults] = useState<Store[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (query.trim().length < 2) return;
    const timer = setTimeout(() => {
      setError(null);
      searchStores(query.trim(), chain || undefined)
        .then(setResults)
        .catch((err) => setError(getErrorMessage(err)));
    }, 300);
    return () => clearTimeout(timer);
  }, [query, chain]);

  const showResults = query.trim().length >= 2;

  return (
    <div className="space-y-3">
      <div className="relative">
        <Search size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-app-text-secondary" aria-hidden />
        <input
          type="search"
          dir="auto"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="City, street or branch name, e.g. אשדוד or הרצל"
          aria-label="Search branches"
          className="h-11 w-full rounded-xl border border-app-border bg-app-surface pl-9 pr-3 text-sm"
        />
      </div>
      <div className="flex flex-wrap gap-2" role="group" aria-label="Filter by chain">
        {[{ slug: '', name: 'All chains' }, ...chains].map((c) => (
          <button
            key={c.slug || 'all'}
            type="button"
            onClick={() => setChain(c.slug)}
            aria-pressed={chain === c.slug}
            className={`h-9 rounded-full border px-3 text-sm font-medium ${
              chain === c.slug ? 'border-accent bg-accent text-on-accent' : 'border-app-border text-app-text-secondary hover:bg-app-hover'
            }`}
          >
            {c.name}
          </button>
        ))}
      </div>

      {error && <p role="alert" className="text-sm text-danger">{error}</p>}
      {showResults && results === null && !error && <Skeleton className="h-32" />}
      {showResults && results?.length === 0 && (
        <p className="text-sm text-app-text-secondary">No branches match. Try the city name in Hebrew.</p>
      )}
      {showResults && results && results.length > 0 && (
        <ul className="divide-y divide-app-border rounded-2xl border border-app-border bg-app-surface">
          {results.map((store) => {
            const followed = followedIds.has(store.id);
            return (
              <li key={store.id} className="flex items-center gap-3 px-4 py-3">
                <div className="min-w-0 flex-1">
                  <p className="text-sm"><span className="font-semibold">{store.chain_name}</span> · <span dir="auto">{store.name}</span></p>
                  {store.address && <p dir="auto" className="truncate text-xs text-app-text-secondary">{store.address}</p>}
                </div>
                {followed ? (
                  <span className="flex items-center gap-1 text-sm font-medium text-success"><Check size={14} aria-hidden /> Yours</span>
                ) : (
                  <Button size="sm" variant="secondary" loading={followingId === store.id} onClick={() => onFollow(store)}>
                    Use this
                  </Button>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
