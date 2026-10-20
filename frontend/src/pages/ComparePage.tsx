import { Save } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import BranchContext from '../components/basket/BranchContext';
import ComparingIndicator from '../components/basket/ComparingIndicator';
import HeroStats from '../components/basket/HeroStats';
import ListInput from '../components/basket/ListInput';
import ResultsView from '../components/basket/ResultsView';
import Button from '../components/ui/Button';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import { useBasketEditing } from '../hooks/useBasketEditing';
import { useDocumentTitle } from '../hooks/useDocumentTitle';
import { useI18n } from '../i18n/LanguageContext';
import { compareList } from '../services/baskets';
import { getMyStores } from '../services/branches';
import { getChains, getDemoStores } from '../services/catalog';
import { compareSavedList, createList, getLists } from '../services/lists';
import type { Chain, SavedList, Store } from '../types';
import { getErrorMessage } from '../utils/errors';

const DRAFT_KEY = 'cartwise_draft';

export default function ComparePage() {
  const { user } = useAuth();
  const { t, date } = useI18n();
  const { showSuccess, showError } = useToast();
  const [params] = useSearchParams();
  const listId = params.get('list');

  const [text, setText] = useState(() => sessionStorage.getItem(DRAFT_KEY) ?? '');
  const [savedList, setSavedList] = useState<SavedList | null>(null);
  const [chains, setChains] = useState<Chain[]>([]);
  const [myStores, setMyStores] = useState<Store[]>([]);
  const [demoStores, setDemoStores] = useState<Store[]>([]);
  const [comparing, setComparing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const { result, setResult, busyLine, confirm, swap } = useBasketEditing(Boolean(user));
  useDocumentTitle(savedList ? savedList.name : t('title.compare'));

  useEffect(() => {
    getChains().then(setChains).catch(() => setChains([]));
    getDemoStores().then((stores) => setDemoStores(stores.filter((s) => s.is_ready))).catch(() => setDemoStores([]));
    if (user) getMyStores().then(setMyStores).catch(() => setMyStores([]));
  }, [user]);

  useEffect(() => {
    if (!listId || !user) return;
    getLists()
      .then((lists) => {
        const found = lists.find((l) => l.id === listId) ?? null;
        setSavedList(found);
        if (found) setText(found.text);
      })
      .catch((err) => setError(getErrorMessage(err, t)));
  }, [listId, user, t]);

  const updateText = (value: string) => {
    setText(value);
    sessionStorage.setItem(DRAFT_KEY, value);
  };

  const runComparison = async () => {
    setComparing(true);
    setError(null);
    setResult(null);
    try {
      setResult(savedList ? await compareSavedList(savedList.id) : await compareList(text));
    } catch (err) {
      setError(getErrorMessage(err, t));
    } finally {
      setComparing(false);
    }
  };

  const saveAsList = async () => {
    setSaving(true);
    try {
      const created = await createList(t('input.defaultListName', { date: date(new Date().toISOString()) }), text);
      showSuccess(t('input.savedAs', { name: created.name }));
    } catch (err) {
      showError(getErrorMessage(err, t));
    } finally {
      setSaving(false);
    }
  };

  const comparedChains = (myStores.length ? myStores : demoStores).map((s) => s.chain_slug);

  return (
    <div className="space-y-6">
      <header className="space-y-5 pb-2 pt-4 text-center md:pt-10">
        <h1 className="text-4xl font-extrabold leading-[1.1] tracking-tight md:text-6xl">
          {savedList ? savedList.name : <>{t('hero.before')} <span className="marker">{t('hero.marker')}</span> {t('hero.after')}</>}
        </h1>
        <p className="mx-auto max-w-xl text-app-text-secondary md:text-lg">{t('hero.subtitle')}</p>
        {!savedList && chains.length > 0 && <HeroStats chains={chains} />}
      </header>

      <BranchContext signedIn={Boolean(user)} myStores={myStores} demoStores={demoStores} />

      <ListInput value={text} onChange={updateText} onSubmit={runComparison} loading={comparing} readOnly={Boolean(savedList)} />

      {savedList && (
        <p className="text-xs text-app-text-secondary">
          {t('input.savedNote')} <Link to="/lists" className="font-semibold text-accent hover:underline">{t('input.editOnLists')}</Link>.
        </p>
      )}
      {user && !savedList && text.trim().length >= 2 && (
        <Button variant="ghost" size="sm" icon={<Save size={14} />} onClick={saveAsList} loading={saving}>
          {t('input.saveAsList')}
        </Button>
      )}

      {comparing && <ComparingIndicator lines={text.split('\n').filter((l) => l.trim())} chains={comparedChains} />}
      {error && <p role="alert" className="rounded-2xl bg-danger/10 px-4 py-3 text-sm text-danger">{error}</p>}
      {result && !comparing && (
        <ResultsView result={result} editable canSave={Boolean(user)} busyLine={busyLine} onConfirm={confirm} onSwap={swap} />
      )}
    </div>
  );
}
