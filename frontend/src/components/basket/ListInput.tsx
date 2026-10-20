import { ShoppingBasket, Wand2 } from 'lucide-react';
import type { FormEvent } from 'react';
import Button from '../ui/Button';

const SAMPLE_LIST = '2 חלב 3%\nביצים L\nחצי קילו עגבניות\nקוטג\' תנובה\nבמבה\nלחם אחיד פרוס\nשמן קנולה';
const MAX_LENGTH = 2000;

interface ListInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  loading: boolean;
  readOnly?: boolean;
}

export default function ListInput({ value, onChange, onSubmit, loading, readOnly = false }: ListInputProps) {
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (value.trim().length >= 2 && !loading) onSubmit();
  };

  return (
    <form onSubmit={handleSubmit} className="rounded-2xl border border-app-border bg-app-surface p-4">
      <label htmlFor="grocery-list" className="text-sm font-semibold">Your grocery list</label>
      <p className="text-xs text-app-text-secondary">One item per line, in Hebrew or English. Quantities like "2" or "חצי קילו" work.</p>
      <textarea
        id="grocery-list"
        dir={value ? 'auto' : 'rtl'}
        rows={7}
        maxLength={MAX_LENGTH}
        value={value}
        readOnly={readOnly}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleSubmit(e);
        }}
        placeholder={'2 חלב 3%\nחצי קילו עגבניות\nbananas 1kg'}
        className="mt-3 w-full resize-y rounded-xl border border-app-border bg-app-bg p-3 text-sm leading-6 placeholder:text-app-text-secondary/60 read-only:opacity-80"
      />
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <Button type="submit" loading={loading} disabled={value.trim().length < 2} icon={<ShoppingBasket size={16} />}>
          Find the cheapest basket
        </Button>
        {!readOnly && !value && (
          <Button type="button" variant="ghost" icon={<Wand2 size={16} />} onClick={() => onChange(SAMPLE_LIST)}>
            Try a sample list
          </Button>
        )}
        <span className="ml-auto font-mono text-xs text-app-text-secondary">{value.length}/{MAX_LENGTH}</span>
      </div>
    </form>
  );
}
