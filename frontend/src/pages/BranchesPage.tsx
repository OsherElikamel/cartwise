import { useCallback, useEffect, useState } from 'react';
import BranchSearch from '../components/branches/BranchSearch';
import MyBranches from '../components/branches/MyBranches';
import Skeleton from '../components/ui/Skeleton';
import { useToast } from '../contexts/ToastContext';
import { useDocumentTitle } from '../hooks/useDocumentTitle';
import { useI18n } from '../i18n/LanguageContext';
import { followStore, getMyStores, unfollowStore } from '../services/branches';
import { getChains } from '../services/catalog';
import type { Chain, Store } from '../types';
import { getErrorMessage } from '../utils/errors';

const POLL_MS = 3000;

export default function BranchesPage() {
  const { t, chain } = useI18n();
  useDocumentTitle(t('title.branches'));
  const { showSuccess, showError } = useToast();
  const [chains, setChains] = useState<Chain[] | null>(null);
  const [myStores, setMyStores] = useState<Store[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [followingId, setFollowingId] = useState<string | null>(null);
  const [removingId, setRemovingId] = useState<string | null>(null);

  const refresh = useCallback(() => getMyStores().then(setMyStores), []);

  useEffect(() => {
    Promise.all([getChains(), getMyStores()])
      .then(([c, mine]) => { setChains(c); setMyStores(mine); })
      .catch((err) => setError(getErrorMessage(err, t)));
  }, [t]);

  // A newly added branch loads its prices in the background; check back until it's ready.
  const loading = myStores.some((s) => !s.is_ready);
  useEffect(() => {
    if (!loading) return;
    const timer = setInterval(() => { refresh().catch(() => undefined); }, POLL_MS);
    return () => clearInterval(timer);
  }, [loading, refresh]);

  const follow = async (store: Store) => {
    setFollowingId(store.id);
    try {
      const followed = await followStore(store.id);
      await refresh();
      const vars = { chain: chain(store.chain_slug), name: store.name };
      showSuccess(followed.is_ready ? t('branches.nowYours', vars) : t('branches.loadingToast', vars));
    } catch (err) {
      showError(getErrorMessage(err, t));
    } finally {
      setFollowingId(null);
    }
  };

  const remove = async (store: Store) => {
    setRemovingId(store.id);
    try {
      await unfollowStore(store.id);
      await refresh();
    } catch (err) {
      showError(getErrorMessage(err, t));
    } finally {
      setRemovingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <header className="pt-2">
        <h1 className="text-3xl font-extrabold tracking-tight">{t('branches.title')}</h1>
        <p className="mt-1 text-sm text-app-text-secondary">{t('branches.subtitle')}</p>
      </header>
      {error && <p role="alert" className="rounded-2xl bg-danger/10 px-4 py-3 text-sm text-danger">{error}</p>}
      {chains === null && !error ? (
        <div className="grid gap-3 sm:grid-cols-2">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-24" />)}</div>
      ) : (
        chains && (
          <>
            <MyBranches chains={chains} myStores={myStores} removingId={removingId} onRemove={remove} />
            <section className="space-y-3">
              <h2 className="text-lg font-semibold">{t('branches.find')}</h2>
              <BranchSearch chains={chains} followedIds={new Set(myStores.map((s) => s.id))} followingId={followingId} onFollow={follow} />
            </section>
          </>
        )
      )}
    </div>
  );
}
