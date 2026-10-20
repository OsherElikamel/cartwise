import { MapPin } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import ChainBranchCard from '../components/branches/ChainBranchCard';
import CityPicker from '../components/branches/CityPicker';
import Skeleton from '../components/ui/Skeleton';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import { useDocumentTitle } from '../hooks/useDocumentTitle';
import { useI18n } from '../i18n/LanguageContext';
import { followStore, getMyStores, unfollowStore } from '../services/branches';
import { getBranchesNear, getLocality, setHomeLocality } from '../services/localities';
import type { ChainBranches, Locality, Store } from '../types';
import { getErrorMessage } from '../utils/errors';

const POLL_MS = 3000;

export default function BranchesPage() {
  const { t, chain, place } = useI18n();
  useDocumentTitle(t('title.branches'));
  const { user, updateUser } = useAuth();
  const { showSuccess, showError } = useToast();
  const [home, setHome] = useState<Locality | null>(null);
  const [homeLoaded, setHomeLoaded] = useState(!user?.home_locality_code);
  const [changingCity, setChangingCity] = useState(false);
  const [branches, setBranches] = useState<ChainBranches[] | null>(null);
  const [myStores, setMyStores] = useState<Store[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const refreshMine = useCallback(() => getMyStores().then(setMyStores), []);

  useEffect(() => {
    refreshMine().catch((err) => setError(getErrorMessage(err, t)));
  }, [refreshMine, t]);

  // The saved home city, once.
  useEffect(() => {
    const code = user?.home_locality_code;
    if (!code) return;
    getLocality(code)
      .then(setHome)
      .catch(() => setHome(null))
      .finally(() => setHomeLoaded(true));
  }, [user?.home_locality_code]);

  useEffect(() => {
    if (!home) return;
    getBranchesNear(home.code)
      .then(setBranches)
      .catch((err) => setError(getErrorMessage(err, t)));
  }, [home, t]);

  // A newly added branch loads its prices in the background; check back until it's ready.
  const loading = myStores.some((s) => !s.is_ready);
  useEffect(() => {
    if (!loading) return;
    const timer = setInterval(() => { refreshMine().catch(() => undefined); }, POLL_MS);
    return () => clearInterval(timer);
  }, [loading, refreshMine]);

  const chooseHome = async (locality: Locality) => {
    setBranches(null);
    setHome(locality);
    setChangingCity(false);
    try {
      await setHomeLocality(locality.code);
      updateUser({ home_locality_code: locality.code });
    } catch (err) {
      showError(getErrorMessage(err, t));
    }
  };

  const follow = async (store: Store) => {
    setBusyId(store.id);
    try {
      const followed = await followStore(store.id);
      await refreshMine();
      const vars = { chain: chain(store.chain_slug), name: store.name };
      showSuccess(followed.is_ready ? t('branches.nowYours', vars) : t('branches.loadingToast', vars));
    } catch (err) {
      showError(getErrorMessage(err, t));
    } finally {
      setBusyId(null);
    }
  };

  const remove = async (store: Store) => {
    setBusyId(store.id);
    try {
      await unfollowStore(store.id);
      await refreshMine();
    } catch (err) {
      showError(getErrorMessage(err, t));
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="space-y-6">
      <header className="pt-2">
        <h1 className="text-3xl font-extrabold tracking-tight">{t('branches.title')}</h1>
        <p className="mt-1 text-sm text-app-text-secondary">{t('branches.subtitle')}</p>
      </header>

      <section className="rounded-3xl border border-app-border bg-app-surface/80 p-5">
        <h2 className="text-sm font-semibold">{t('branches.cityLabel')}</h2>
        {home && !changingCity ? (
          <div className="mt-2 flex items-center gap-2">
            <MapPin size={18} className="text-accent" aria-hidden />
            <span className="text-xl font-bold">{place(home)}</span>
            <button type="button" onClick={() => setChangingCity(true)} className="ms-auto text-sm font-semibold text-accent hover:underline">
              {t('context.change')}
            </button>
          </div>
        ) : (
          <div className="mt-2 space-y-2">
            <p className="text-xs text-app-text-secondary">{t('branches.cityHelp')}</p>
            <CityPicker label={t('branches.cityAria')} onSelect={chooseHome} autoFocus={changingCity} />
          </div>
        )}
      </section>

      {error && <p role="alert" className="rounded-2xl bg-danger/10 px-4 py-3 text-sm text-danger">{error}</p>}
      {!homeLoaded && <Skeleton className="h-40" />}
      {homeLoaded && !home && <p className="text-sm text-app-text-secondary">{t('branches.chooseCityFirst')}</p>}
      {home && !branches && !error && <div className="grid gap-3">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-40" />)}</div>}

      {home && branches && (
        <>
          <ul className="grid gap-4 md:grid-cols-2">
            {branches.map((b) => (
              <ChainBranchCard
                key={b.chain_slug}
                branches={b}
                home={home}
                current={myStores.find((s) => s.chain_slug === b.chain_slug)}
                busyId={busyId}
                onFollow={follow}
                onRemove={remove}
              />
            ))}
          </ul>
          <p className="text-xs text-app-text-secondary">{t('branches.distanceNote')}</p>
        </>
      )}
    </div>
  );
}
