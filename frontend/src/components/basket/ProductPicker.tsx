import { Search, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useI18n } from '../../i18n/LanguageContext';
import { searchProducts } from '../../services/catalog';
import type { Alternative } from '../../types';
import { getErrorMessage } from '../../utils/errors';

interface ProductPickerProps {
  storeId: string;
  chainSlug: string;
  suggestions: Alternative[];
  busy: boolean;
  onPick: (alt: Alternative) => void;
  onClose: () => void;
}

const MIN_QUERY = 2;

/** The AI's suggestions, plus a free-text search of this branch's shelves for
 *  when none of them is what the shopper meant. */
export default function ProductPicker({ storeId, chainSlug, suggestions, busy, onPick, onClose }: ProductPickerProps) {
  const { t, price, chain } = useI18n();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Alternative[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const searching = query.trim().length >= MIN_QUERY;

  useEffect(() => {
    if (query.trim().length < MIN_QUERY) return;
    const timer = setTimeout(() => {
      setError(null);
      searchProducts(query.trim(), storeId)
        .then((rows) => setResults(rows.map((r) => ({ item_code: r.item_code, name: r.name, price: r.price }))))
        .catch((err) => setError(getErrorMessage(err, t)));
    }, 300);
    return () => clearTimeout(timer);
  }, [query, storeId, t]);

  const shown = searching ? results : suggestions;

  return (
    <div className="ms-[4.75rem] mt-2 overflow-hidden rounded-2xl border border-app-border bg-app-bg/40" onKeyDown={(e) => e.key === 'Escape' && onClose()}>
      <div className="flex items-center gap-2 border-b border-app-border px-3">
        <Search size={15} className="shrink-0 text-app-text-secondary" aria-hidden />
        <input
          type="search"
          dir="auto"
          autoFocus
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={t('line.searchPlaceholder')}
          aria-label={t('line.searchAria', { chain: chain(chainSlug) })}
          className="h-11 min-w-0 flex-1 bg-transparent text-sm outline-none"
        />
        <button type="button" onClick={onClose} aria-label={t('line.close')} className="flex h-8 w-8 items-center justify-center rounded-full text-app-text-secondary hover:bg-app-hover">
          <X size={15} />
        </button>
      </div>
      {!searching && suggestions.length > 0 && (
        <p className="px-3 pt-2 text-xs font-medium text-app-text-secondary">{t('line.suggestions')}</p>
      )}
      {error && <p role="alert" className="px-3 py-2 text-sm text-danger">{error}</p>}
      {searching && results?.length === 0 && <p className="px-3 py-3 text-sm text-app-text-secondary">{t('line.noResults')}</p>}
      {shown && shown.length > 0 && (
        <ul className="max-h-72 divide-y divide-app-border overflow-y-auto">
          {shown.map((alt) => (
            <li key={alt.item_code}>
              <button
                type="button"
                disabled={busy}
                onClick={() => onPick(alt)}
                className="flex w-full items-center gap-3 px-3 py-2.5 text-start hover:bg-app-hover disabled:opacity-60"
              >
                <span dir="auto" className="min-w-0 flex-1 text-sm">{alt.name}</span>
                <span className="font-mono text-sm">{price(alt.price)}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
