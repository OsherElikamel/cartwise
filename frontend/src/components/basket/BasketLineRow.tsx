import { AlertTriangle, ArrowLeftRight, BookmarkCheck, Check, Tag } from 'lucide-react';
import { useState } from 'react';
import { useI18n } from '../../i18n/LanguageContext';
import type { Alternative, BasketLine, ParsedItem } from '../../types';
import Badge from '../ui/Badge';
import Button from '../ui/Button';

interface BasketLineRowProps {
  line: BasketLine;
  item: ParsedItem;
  editable: boolean;
  canSave: boolean;
  busy: boolean;
  onConfirm?: () => void;
  onSwap?: (alt: Alternative) => void;
}

export default function BasketLineRow({ line, item, editable, canSave, busy, onConfirm, onSwap }: BasketLineRowProps) {
  const { t, price, quantity } = useI18n();
  const [showAlternatives, setShowAlternatives] = useState(false);
  const missing = line.item_code === null;
  const unsure = line.confidence === 'low';
  const canSwap = editable && onSwap && line.alternatives.length > 0;

  return (
    <li className="py-3">
      <div className="flex items-start gap-3">
        <span className="w-16 shrink-0 whitespace-nowrap pt-0.5 font-mono text-sm text-app-text-secondary">
          {quantity(item.quantity, item.unit)}
        </span>
        <div className="min-w-0 flex-1">
          <p dir="auto" className={`text-sm font-semibold ${missing ? 'text-app-text-secondary line-through' : ''}`}>
            {line.name ?? item.original}
          </p>
          <p className="truncate text-xs text-app-text-secondary">
            {missing ? t('line.notFound') : <>{t('line.youWrote')} <bdi>{item.original}</bdi></>}
          </p>
          <div className="mt-1.5 flex flex-wrap gap-1.5">
            {line.deal && <Badge tone="deal" icon={<Tag size={11} />} title={line.deal}>{t('line.deal')}</Badge>}
            {unsure && <Badge tone="warning" icon={<AlertTriangle size={11} />}>{t('line.checkThis')}</Badge>}
            {line.confidence === 'remembered' && <Badge tone="success" icon={<BookmarkCheck size={11} />}>{t('line.yourChoice')}</Badge>}
          </div>
        </div>
        <span className="shrink-0 pt-0.5 font-mono text-sm font-bold">
          {line.line_total ? price(line.line_total) : '—'}
        </span>
      </div>

      {editable && (unsure || missing) && (canSave || canSwap) && (
        <div className="mt-2 flex flex-wrap gap-2 ps-[4.75rem]">
          {unsure && canSave && onConfirm && (
            <Button size="sm" variant="secondary" icon={<Check size={14} />} onClick={onConfirm} loading={busy}>
              {t('line.looksRight')}
            </Button>
          )}
          {canSwap && (
            <Button size="sm" variant="secondary" icon={<ArrowLeftRight size={14} />} onClick={() => setShowAlternatives((s) => !s)} aria-expanded={showAlternatives}>
              {missing ? t('line.pickProduct') : t('line.swap')}
            </Button>
          )}
        </div>
      )}
      {editable && !unsure && !missing && canSwap && (
        <button
          type="button"
          onClick={() => setShowAlternatives((s) => !s)}
          aria-expanded={showAlternatives}
          className="ms-[4.75rem] mt-1 text-xs font-medium text-app-text-secondary underline-offset-2 hover:text-app-text hover:underline"
        >
          {t('line.notRight')}
        </button>
      )}

      {showAlternatives && onSwap && (
        <ul className="ms-[4.75rem] mt-2 divide-y divide-app-border overflow-hidden rounded-2xl border border-app-border">
          {line.alternatives.map((alt) => (
            <li key={alt.item_code}>
              <button
                type="button"
                disabled={busy}
                onClick={() => { setShowAlternatives(false); onSwap(alt); }}
                className="flex w-full items-center gap-3 px-3 py-2.5 text-start hover:bg-app-hover disabled:opacity-60"
              >
                <span dir="auto" className="min-w-0 flex-1 text-sm">{alt.name}</span>
                <span className="font-mono text-sm">{price(alt.price)}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </li>
  );
}
