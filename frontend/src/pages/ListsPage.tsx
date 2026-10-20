import { ListChecks, Pencil, Plus, ShoppingBasket, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ListEditor from '../components/basket/ListEditor';
import Button from '../components/ui/Button';
import EmptyState from '../components/ui/EmptyState';
import Skeleton from '../components/ui/Skeleton';
import { useToast } from '../contexts/ToastContext';
import { useDocumentTitle } from '../hooks/useDocumentTitle';
import { useI18n } from '../i18n/LanguageContext';
import { createList, deleteList, getLists, updateList } from '../services/lists';
import type { SavedList } from '../types';
import { getErrorMessage } from '../utils/errors';

export default function ListsPage() {
  const { t, date } = useI18n();
  useDocumentTitle(t('title.lists'));
  const navigate = useNavigate();
  const { showSuccess, showError } = useToast();
  const [lists, setLists] = useState<SavedList[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | 'new' | null>(null);
  const [confirmingDeleteId, setConfirmingDeleteId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getLists().then(setLists).catch((err) => setError(getErrorMessage(err, t)));
  }, [t]);

  const save = async (name: string, text: string) => {
    setSaving(true);
    try {
      if (editingId === 'new') {
        const created = await createList(name, text);
        setLists((ls) => [created, ...(ls ?? [])]);
      } else if (editingId) {
        const updated = await updateList(editingId, { name, text });
        setLists((ls) => ls?.map((l) => (l.id === updated.id ? updated : l)) ?? null);
      }
      setEditingId(null);
      showSuccess(t('lists.saved'));
    } catch (err) {
      showError(getErrorMessage(err, t));
    } finally {
      setSaving(false);
    }
  };

  const remove = async (id: string) => {
    try {
      await deleteList(id);
      setLists((ls) => ls?.filter((l) => l.id !== id) ?? null);
      showSuccess(t('lists.deleted'));
    } catch (err) {
      showError(getErrorMessage(err, t));
    } finally {
      setConfirmingDeleteId(null);
    }
  };

  return (
    <div className="space-y-5">
      <header className="flex items-start gap-3 pt-2">
        <div className="flex-1">
          <h1 className="text-3xl font-extrabold tracking-tight">{t('lists.title')}</h1>
          <p className="mt-1 text-sm text-app-text-secondary">{t('lists.subtitle')}</p>
        </div>
        {editingId !== 'new' && <Button icon={<Plus size={16} />} onClick={() => setEditingId('new')}>{t('lists.new')}</Button>}
      </header>

      {editingId === 'new' && <ListEditor submitLabel={t('lists.create')} saving={saving} onSave={save} onCancel={() => setEditingId(null)} />}
      {error && <p role="alert" className="rounded-2xl bg-danger/10 px-4 py-3 text-sm text-danger">{error}</p>}
      {lists === null && !error && <div className="space-y-3"><Skeleton className="h-28" /><Skeleton className="h-28" /></div>}
      {lists?.length === 0 && editingId !== 'new' && (
        <EmptyState icon={<ListChecks size={40} />} title={t('lists.emptyTitle')}>
          {t('lists.emptyBody')}
        </EmptyState>
      )}

      <ul className="space-y-3">
        {lists?.map((list) =>
          editingId === list.id ? (
            <li key={list.id}>
              <ListEditor initialName={list.name} initialText={list.text} submitLabel={t('lists.saveChanges')} saving={saving} onSave={save} onCancel={() => setEditingId(null)} />
            </li>
          ) : (
            <li key={list.id} className="rounded-3xl border border-app-border bg-app-surface/80 p-5">
              <div className="flex items-baseline gap-2">
                <h2 dir="auto" className="flex-1 font-semibold">{list.name}</h2>
                <span className="text-xs text-app-text-secondary">{t('lists.updated', { date: date(list.updated_at) })}</span>
              </div>
              <p dir="auto" className="mt-1 line-clamp-2 whitespace-pre-line text-sm text-app-text-secondary">{list.text}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                <Button size="sm" icon={<ShoppingBasket size={14} />} onClick={() => navigate(`/?list=${list.id}`)}>{t('lists.compare')}</Button>
                <Button size="sm" variant="secondary" icon={<Pencil size={14} />} onClick={() => setEditingId(list.id)}>{t('lists.edit')}</Button>
                {confirmingDeleteId === list.id ? (
                  <>
                    <Button size="sm" variant="ghost" onClick={() => setConfirmingDeleteId(null)}>{t('lists.cancel')}</Button>
                    <Button size="sm" variant="danger" onClick={() => remove(list.id)}>{t('lists.deleteForGood')}</Button>
                  </>
                ) : (
                  <Button size="sm" variant="ghost" icon={<Trash2 size={14} />} onClick={() => setConfirmingDeleteId(list.id)} aria-label={t('lists.deleteAria', { name: list.name })}>
                    {t('lists.delete')}
                  </Button>
                )}
              </div>
            </li>
          ),
        )}
      </ul>
    </div>
  );
}
