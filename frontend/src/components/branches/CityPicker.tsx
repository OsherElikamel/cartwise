import { MapPin, Search } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useI18n } from '../../i18n/LanguageContext';
import { searchLocalities } from '../../services/localities';
import type { Locality } from '../../types';
import { getErrorMessage } from '../../utils/errors';

interface CityPickerProps {
  label: string;
  onSelect: (locality: Locality) => void;
  autoFocus?: boolean;
}

/** Type-ahead over the official list of localities, in Hebrew or English. */
export default function CityPicker({ label, onSelect, autoFocus = false }: CityPickerProps) {
  const { t, place, lang } = useI18n();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Locality[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const active = query.trim().length >= 1;

  useEffect(() => {
    if (!query.trim()) return;
    const timer = setTimeout(() => {
      setError(null);
      searchLocalities(query.trim())
        .then(setResults)
        .catch((err) => setError(getErrorMessage(err, t)));
    }, 250);
    return () => clearTimeout(timer);
  }, [query, t]);

  return (
    <div className="space-y-2">
      <div className="relative">
        <Search size={16} className="pointer-events-none absolute start-4 top-1/2 -translate-y-1/2 text-app-text-secondary" aria-hidden />
        <input
          type="search"
          dir="auto"
          autoFocus={autoFocus}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={t('branches.cityPlaceholder')}
          aria-label={label}
          className="h-12 w-full rounded-full border border-app-border bg-app-surface/80 pe-4 ps-11 text-sm"
        />
      </div>
      {error && <p role="alert" className="text-sm text-danger">{error}</p>}
      {active && results?.length === 0 && <p className="px-2 text-sm text-app-text-secondary">{t('branches.noCities')}</p>}
      {active && results && results.length > 0 && (
        <ul className="divide-y divide-app-border overflow-hidden rounded-2xl border border-app-border bg-app-surface/90">
          {results.map((loc) => (
            <li key={loc.code}>
              <button
                type="button"
                onClick={() => { onSelect(loc); setQuery(''); setResults(null); }}
                className="flex w-full items-center gap-3 px-4 py-3 text-start hover:bg-app-hover"
              >
                <MapPin size={15} className="shrink-0 text-app-text-secondary" aria-hidden />
                <span className="text-sm font-medium">{place(loc)}</span>
                <span className="text-xs text-app-text-secondary" lang={lang === 'he' ? 'en' : 'he'}>
                  {lang === 'he' ? loc.name_en : loc.name_he}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
