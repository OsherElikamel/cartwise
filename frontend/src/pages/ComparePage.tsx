import { Save } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import BranchContext from '../components/basket/BranchContext';
import ComparingIndicator from '../components/basket/ComparingIndicator';
import ListInput from '../components/basket/ListInput';
import ResultsView from '../components/basket/ResultsView';
import Button from '../components/ui/Button';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import { useBasketEditing } from '../hooks/useBasketEditing';
import { useDocumentTitle } from '../hooks/useDocumentTitle';
import { compareList } from '../services/baskets';
import { getMyStores } from '../services/branches';
import { getDemoStores } from '../services/catalog';
import { compareSavedList, createList, getLists } from '../services/lists';
import type { SavedList, Store } from '../types';
import { getErrorMessage } from '../utils/errors';

const DRAFT_KEY = 'cartwise_draft';

export default function ComparePage() {
  const { user } = useAuth();
  const { showSuccess, showError } = useToast();
  const [params] = useSearchParams();
  const listId = params.get('list');

  const [text, setText] = useState(() => sessionStorage.getItem(DRAFT_KEY) ?? '');
  const [savedList, setSavedList] = useState<SavedList | null>(null);
  const [myStores, setMyStores] = useState<Store[]>([]);
  const [demoStores, setDemoStores] = useState<Store[]>([]);
  const [comparing, setComparing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const { result, setResult, busyLine, confirm, swap } = useBasketEditing(Boolean(user));
  useDocumentTitle(savedList ? savedList.name : 'Compare');

  useEffect(() => {
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
      .catch((err) => setError(getErrorMessage(err)));
  }, [listId, user]);

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
      setError(getErrorMessage(err));
    } finally {
      setComparing(false);
    }
  };

  const saveAsList = async () => {
    setSaving(true);
    try {
      const created = await createList(`List of ${new Date().toLocaleDateString('en-GB')}`, text);
      showSuccess(`Saved as "${created.name}". Rename it on the Lists page.`);
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-2xl font-bold tracking-tight md:text-3xl">
          {savedList ? savedList.name : <>Which supermarket is <span className="marker">cheapest</span> for your list?</>}
        </h1>
        <p className="mt-1 text-sm text-app-text-secondary">
          Real prices from the files every chain publishes by law, compared item by item.
        </p>
      </header>

      <BranchContext signedIn={Boolean(user)} myStores={myStores} demoStores={demoStores} />

      <ListInput value={text} onChange={updateText} onSubmit={runComparison} loading={comparing} readOnly={Boolean(savedList)} />

      {savedList && (
        <p className="text-xs text-app-text-secondary">
          This is a saved list. <Link to="/lists" className="font-semibold text-accent hover:underline">Edit it on the Lists page</Link>.
        </p>
      )}
      {user && !savedList && text.trim().length >= 2 && (
        <Button variant="ghost" size="sm" icon={<Save size={14} />} onClick={saveAsList} loading={saving}>
          Save as a list
        </Button>
      )}

      {comparing && <ComparingIndicator />}
      {error && <p role="alert" className="rounded-2xl bg-danger/10 px-4 py-3 text-sm text-danger">{error}</p>}
      {result && !comparing && (
        <ResultsView result={result} editable canSave={Boolean(user)} busyLine={busyLine} onConfirm={confirm} onSwap={swap} />
      )}
    </div>
  );
}
