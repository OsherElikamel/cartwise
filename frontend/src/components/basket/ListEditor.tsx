import { useState, type FormEvent } from 'react';
import { useI18n } from '../../i18n/LanguageContext';
import Button from '../ui/Button';

interface ListEditorProps {
  initialName?: string;
  initialText?: string;
  submitLabel: string;
  saving: boolean;
  onSave: (name: string, text: string) => void;
  onCancel: () => void;
}

export default function ListEditor({ initialName = '', initialText = '', submitLabel, saving, onSave, onCancel }: ListEditorProps) {
  const { t } = useI18n();
  const [name, setName] = useState(initialName);
  const [text, setText] = useState(initialText);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (name.trim() && text.trim().length >= 2) onSave(name.trim(), text);
  };

  return (
    <form onSubmit={handleSubmit} onKeyDown={(e) => e.key === 'Escape' && onCancel()} className="space-y-3 rounded-3xl border border-app-border bg-app-surface/80 p-5">
      <div>
        <label htmlFor="list-name" className="text-sm font-medium">{t('lists.nameLabel')}</label>
        <input id="list-name" dir="auto" value={name} maxLength={100} onChange={(e) => setName(e.target.value)} placeholder={t('lists.namePlaceholder')}
          className="mt-1 h-11 w-full rounded-xl border border-app-border bg-app-bg/60 px-3 text-sm" />
      </div>
      <div>
        <label htmlFor="list-text" className="text-sm font-medium">{t('lists.itemsLabel')}</label>
        <textarea id="list-text" dir="auto" rows={6} maxLength={2000} value={text} onChange={(e) => setText(e.target.value)}
          className="mt-1 w-full rounded-2xl border border-app-border bg-app-bg/60 p-3 text-sm leading-6" />
      </div>
      <div className="flex gap-2">
        <Button type="submit" loading={saving} disabled={!name.trim() || text.trim().length < 2}>{submitLabel}</Button>
        <Button type="button" variant="ghost" onClick={onCancel}>{t('lists.cancel')}</Button>
      </div>
    </form>
  );
}
