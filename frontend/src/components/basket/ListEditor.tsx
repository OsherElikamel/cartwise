import { useState, type FormEvent } from 'react';
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
  const [name, setName] = useState(initialName);
  const [text, setText] = useState(initialText);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (name.trim() && text.trim().length >= 2) onSave(name.trim(), text);
  };

  return (
    <form onSubmit={handleSubmit} onKeyDown={(e) => e.key === 'Escape' && onCancel()} className="space-y-3 rounded-2xl border border-app-border bg-app-surface p-4">
      <div>
        <label htmlFor="list-name" className="text-sm font-medium">Name</label>
        <input id="list-name" value={name} maxLength={100} onChange={(e) => setName(e.target.value)} placeholder="Weekly shop"
          className="mt-1 h-11 w-full rounded-xl border border-app-border bg-app-bg px-3 text-sm" />
      </div>
      <div>
        <label htmlFor="list-text" className="text-sm font-medium">Items, one per line</label>
        <textarea id="list-text" dir="auto" rows={6} maxLength={2000} value={text} onChange={(e) => setText(e.target.value)}
          className="mt-1 w-full rounded-xl border border-app-border bg-app-bg p-3 text-sm leading-6" />
      </div>
      <div className="flex gap-2">
        <Button type="submit" loading={saving} disabled={!name.trim() || text.trim().length < 2}>{submitLabel}</Button>
        <Button type="button" variant="ghost" onClick={onCancel}>Cancel</Button>
      </div>
    </form>
  );
}
