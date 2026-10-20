import { Check, Search } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useI18n } from '../../i18n/LanguageContext';
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
  const { t, chain: chainName } = useI18n();
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
        .catch((err) => setError(getErrorMessage(err, t)));
    }, 300);
    return () => clearTimeout(timer);
  }, [query, chain, t]);

  const showResults = query.trim().length >= 2;

  return (
    <div className="space-y-3">
      <div className="relative">
        <Search size={16} className="pointer-events-none absolute start-4 top-1/2 -translate-y-1/2 text-app-text-secondary" aria-hidden />
        <input
          type="search"
          dir="auto"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={t('branches.searchPlaceholder')}
          aria-label={t('branches.searchAria')}
          className="h-12 w-full rounded-full border border-app-border bg-app-surface/80 pe-4 ps-11 text-sm"
        />
      </div>
      <div className="flex flex-wrap gap-2" role="group" aria-label={t('branches.filterAria')}>
        {[{ slug: '', label: t('branches.allChains') }, ...chains.map((c) => ({ slug: c.slug, label: chainName(c.slug) }))].map((c) => (
          <button
            key={c.slug || 'all'}
            type="button"
            onClick={() => setChain(c.slug)}
            aria-pressed={chain === c.slug}
            className={`h-9 rounded-full border px-4 text-sm font-medium ${
              chain === c.slug ? 'border-transparent bg-app-text text-app-bg' : 'border-app-border text-app-text-secondary hover:bg-app-hover'
            }`}
          >
            {c.label}
          </button>
        ))}
      </div>

      {error && <p role="alert" className="text-sm text-danger">{error}</p>}
      {showResults && results === null && !error && <Skeleton className="h-32" />}
      {showResults && results?.length === 0 && <p className="text-sm text-app-text-secondary">{t('branches.noMatch')}</p>}
      {showResults && results && results.length > 0 && (
        <ul className="divide-y divide-app-border overflow-hidden rounded-3xl border border-app-border bg-app-surface/80">
          {results.map((store) => (
            <li key={store.id} className="flex items-center gap-3 px-4 py-3">
              <div className="min-w-0 flex-1">
                <p className="text-sm"><span className="font-semibold">{chainName(store.chain_slug)}</span> · <bdi>{store.name}</bdi></p>
                {store.address && <p dir="auto" className="truncate text-xs text-app-text-secondary">{store.address}</p>}
              </div>
              {followedIds.has(store.id) ? (
                <span className="flex items-center gap-1 text-sm font-medium text-success"><Check size={14} aria-hidden /> {t('branches.yours')}</span>
              ) : (
                <Button size="sm" variant="secondary" loading={followingId === store.id} onClick={() => onFollow(store)}>
                  {t('branches.useThis')}
                </Button>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
