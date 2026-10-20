import { AlertTriangle, ArrowLeftRight, BookmarkCheck, Check, Scale, Tag } from 'lucide-react';
import { useState } from 'react';
import { useI18n } from '../../i18n/LanguageContext';
import type { Alternative, BasketLine, ParsedItem } from '../../types';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import ProductPicker from './ProductPicker';

interface BasketLineRowProps {
  line: BasketLine;
  storeId: string;
  chainSlug: string;
  item: ParsedItem;
  editable: boolean;
  canSave: boolean;
  busy: boolean;
  onConfirm?: () => void;
  onSwap?: (alt: Alternative) => void;
}

export default function BasketLineRow({ line, storeId, chainSlug, item, editable, canSave, busy, onConfirm, onSwap }: BasketLineRowProps) {
  const { t, price, quantity } = useI18n();
  const [showAlternatives, setShowAlternatives] = useState(false);
  const missing = line.item_code === null;
  const unsure = line.confidence === 'low';
  const canSwap = editable && Boolean(onSwap);

  return (
    <li className="py-3">
      <div className="flex items-start gap-3">
        <span className="w-16 shrink-0 whitespace-nowrap pt-0.5 font-mono text-sm text-app-text-secondary">
          {quantity(item.quantity, item.unit)}
          {line.estimated_kg && <span className="block text-xs">{t('line.estimatedKg', { kg: Number(line.estimated_kg) })}</span>}
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
            {line.estimated_kg && (
              <Badge tone="neutral" icon={<Scale size={11} />} title={t('line.estimatedTitle', { kg: Number(line.estimated_kg) })}>
                {t('line.estimated')}
              </Badge>
            )}
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
        <ProductPicker
          storeId={storeId}
          chainSlug={chainSlug}
          suggestions={line.alternatives}
          busy={busy}
          onPick={(alt) => { setShowAlternatives(false); onSwap(alt); }}
          onClose={() => setShowAlternatives(false)}
        />
      )}
    </li>
  );
}
