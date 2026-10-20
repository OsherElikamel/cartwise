import { Check, Loader2, MapPin, X } from 'lucide-react';
import { useState } from 'react';
import { useI18n } from '../../i18n/LanguageContext';
import { getBranchesNear } from '../../services/localities';
import type { ChainBranches, Locality, Store } from '../../types';
import { getErrorMessage } from '../../utils/errors';
import Button from '../ui/Button';
import Skeleton from '../ui/Skeleton';
import CityPicker from './CityPicker';

interface ChainBranchCardProps {
  branches: ChainBranches;
  home: Locality;
  current: Store | undefined;
  busyId: string | null;
  onFollow: (store: Store) => void;
  onRemove: (store: Store) => void;
}

function StoreRow({ store, isCurrent, busy, onFollow }: { store: Store; isCurrent: boolean; busy: boolean; onFollow: () => void }) {
  const { t } = useI18n();
  return (
    <li className="flex items-center gap-3 py-2.5">
      <div className="min-w-0 flex-1">
        <p dir="auto" className="truncate text-sm font-medium">{store.name}</p>
        {store.address && <p dir="auto" className="truncate text-xs text-app-text-secondary">{store.address}</p>}
      </div>
      {isCurrent ? (
        <span className="flex shrink-0 items-center gap-1 text-sm font-medium text-success"><Check size={14} aria-hidden /> {t('branches.yours')}</span>
      ) : (
        <Button size="sm" variant="secondary" loading={busy} onClick={onFollow}>{t('branches.useThis')}</Button>
      )}
    </li>
  );
}

/** One chain: the branch you use, then branches in your city or the nearest ones. */
export default function ChainBranchCard({ branches, home, current, busyId, onFollow, onRemove }: ChainBranchCardProps) {
  const { t, chain, place } = useI18n();
  const [area, setArea] = useState<{ locality: Locality; data: ChainBranches | null } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const shown = area?.data ?? branches;
  const city = area?.locality ?? home;
  const name = chain(branches.chain_slug);

  const chooseArea = (locality: Locality) => {
    setArea({ locality, data: null });
    setError(null);
    getBranchesNear(locality.code, branches.chain_slug)
      .then(([data]) => setArea({ locality, data: data ?? { ...branches, in_city: [], nearby: [] } }))
      .catch((err) => setError(getErrorMessage(err, t)));
  };

  const row = (store: Store) => (
    <StoreRow key={store.id} store={store} isCurrent={current?.id === store.id} busy={busyId === store.id} onFollow={() => onFollow(store)} />
  );

  return (
    <li className="rounded-3xl border border-app-border bg-app-surface/80 p-5">
      <div className="flex items-start gap-2">
        <div className="min-w-0 flex-1">
          <h2 className="text-lg font-bold">{name}</h2>
          {current ? (
            <p className="mt-0.5 text-sm text-app-text-secondary">
              {t('branches.current')}: <bdi className="font-medium text-app-text">{current.name}</bdi>
              {!current.is_ready && (
                <span className="ms-2 inline-flex items-center gap-1 text-xs text-warning">
                  <Loader2 size={12} className="animate-spin" aria-hidden /> {t('branches.loading')}
                </span>
              )}
            </p>
          ) : (
            <p className="mt-0.5 text-sm text-app-text-secondary">{t('branches.notChosen')}</p>
          )}
        </div>
        {current && (
          <button
            type="button"
            onClick={() => onRemove(current)}
            disabled={busyId === current.id}
            aria-label={t('branches.removeAria', { chain: name, name: current.name })}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-app-text-secondary hover:bg-app-hover hover:text-app-text disabled:opacity-50"
          >
            <X size={16} />
          </button>
        )}
      </div>

      <div className="receipt-rule my-4" />

      {area && !area.data && !error && <Skeleton className="h-24" />}
      {error && <p role="alert" className="text-sm text-danger">{error}</p>}

      {(!area || area.data) && (
        shown.in_city.length > 0 ? (
          <>
            <p className="text-xs font-semibold uppercase tracking-wide text-app-text-secondary">{t('branches.inCity', { city: place(city) })}</p>
            <ul className="divide-y divide-app-border">{shown.in_city.map(row)}</ul>
          </>
        ) : (
          <>
            <p className="flex items-center gap-1.5 text-sm text-app-text-secondary">
              <MapPin size={14} aria-hidden />
              {shown.nearby.length > 0 ? t('branches.noneInCity', { chain: name, city: place(city) }) : t('branches.noNearby', { chain: name })}
            </p>
            {shown.nearby.map((group) => (
              <div key={group.locality.code} className="mt-3">
                <p className="flex items-baseline gap-2 text-xs font-semibold uppercase tracking-wide text-app-text-secondary">
                  {place(group.locality)}
                  <span className="font-mono normal-case">{t('branches.distance', { km: group.distance_km })}</span>
                </p>
                <ul className="divide-y divide-app-border">{group.stores.map(row)}</ul>
              </div>
            ))}
          </>
        )
      )}

      <div className="mt-4">
        {area ? (
          <button type="button" onClick={() => setArea(null)} className="text-sm font-semibold text-accent hover:underline">
            {t('branches.backTo', { city: place(home) })}
          </button>
        ) : (
          <details className="group">
            <summary className="cursor-pointer list-none text-sm font-semibold text-accent hover:underline">{t('branches.otherArea')}</summary>
            <div className="mt-3">
              <CityPicker label={t('branches.otherAreaFor', { chain: name })} onSelect={chooseArea} autoFocus />
            </div>
          </details>
        )}
      </div>
    </li>
  );
}
