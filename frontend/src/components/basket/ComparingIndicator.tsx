import { Loader2 } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useI18n } from '../../i18n/LanguageContext';
import { isolate, itemName } from '../../utils/text';

interface ComparingIndicatorProps {
  /** The user's own list lines. */
  lines: string[];
  /** Chain slugs being compared. */
  chains: string[];
}

const READING_MS = 2500;
const SEARCH_STEP_MS = 1100;
const CHOOSE_STEP_MS = 2300;

/**
 * Shows the real pipeline, in its real order, with the user's own items and
 * stores: reading the list, searching each store's shelves, then the AI
 * choosing products. The server doesn't stream progress, so the steps follow
 * the typical timing rather than live events.
 */
export default function ComparingIndicator({ lines, chains }: ComparingIndicatorProps) {
  const { t, tp, chain } = useI18n();
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const start = Date.now();
    const timer = setInterval(() => setElapsed(Date.now() - start), 250);
    return () => clearInterval(timer);
  }, []);

  const { searching, choosing } = useMemo(() => {
    const items = lines.map(itemName).filter(Boolean).slice(0, 6);
    const names = chains.length ? chains.map(chain) : [''];
    const pairs = items.map((item, i) => ({ item: isolate(item), chain: names[i % names.length] }));
    return {
      searching: [
        ...pairs.map((p) => t('progress.searching', p)),
        ...names.filter(Boolean).map((c) => t('progress.deals', { chain: c })),
      ],
      choosing: pairs.map((p) => t('progress.choosing', p)),
    };
  }, [lines, chains, chain, t]);

  const searchEnd = READING_MS + searching.length * SEARCH_STEP_MS;
  let message: string;
  if (elapsed < READING_MS || searching.length === 0) {
    message = tp('progress.reading', lines.length);
  } else if (elapsed < searchEnd) {
    message = searching[Math.floor((elapsed - READING_MS) / SEARCH_STEP_MS)];
  } else {
    message = choosing[Math.floor((elapsed - searchEnd) / CHOOSE_STEP_MS) % Math.max(choosing.length, 1)] ?? '';
  }
  const aiPhase = elapsed >= searchEnd && searching.length > 0;

  return (
    <div role="status" className="rounded-3xl border border-app-border bg-app-surface/70 p-5">
      <div className="flex items-center gap-3">
        <Loader2 size={18} className="shrink-0 animate-spin text-accent" aria-hidden />
        <span className="text-sm">{message}</span>
      </div>
      {aiPhase && <p className="mt-2 ps-[1.875rem] text-xs text-app-text-secondary">{t('progress.aiNote')}</p>}
    </div>
  );
}
