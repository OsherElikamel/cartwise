import { useI18n } from '../../i18n/LanguageContext';
import type { Alternative, BasketLine, ParsedItem, StoreBasket } from '../../types';
import BasketLineRow from './BasketLineRow';

interface StoreReceiptProps {
  store: StoreBasket;
  items: ParsedItem[];
  sharedItems: number[];
  editable: boolean;
  canSave: boolean;
  busyLine: string | null;
  onConfirm?: (line: BasketLine) => void;
  onSwap?: (line: BasketLine, alt: Alternative) => void;
}

export default function StoreReceipt({
  store, items, sharedItems, editable, canSave, busyLine, onConfirm, onSwap,
}: StoreReceiptProps) {
  const { t, tp, price, chain, dateTime } = useI18n();
  const hasExtras = store.full_total !== store.shared_total;
  return (
    <section aria-label={t('results.receiptAria', { chain: chain(store.chain_slug) })} className="rounded-3xl border border-app-border bg-app-surface p-4 md:p-6">
      <header className="mb-1 text-center">
        <p className="font-mono text-sm font-bold uppercase tracking-widest">{chain(store.chain_slug)}</p>
        <p dir="auto" className="text-center text-xs text-app-text-secondary">{store.store_name}</p>
        {store.prices_updated_at && (
          <p className="mt-0.5 font-mono text-[0.7rem] text-app-text-secondary">
            {t('results.pricesFrom', { when: dateTime(store.prices_updated_at) })}
          </p>
        )}
      </header>
      <div className="receipt-rule my-3" />
      <ul className="divide-y divide-app-border">
        {store.lines.map((line) => (
          <BasketLineRow
            key={line.index}
            line={line}
            storeId={store.store_id}
            chainSlug={store.chain_slug}
            item={items[line.index]}
            editable={editable}
            canSave={canSave}
            busy={busyLine === `${store.store_id}:${line.index}`}
            onConfirm={onConfirm ? () => onConfirm(line) : undefined}
            onSwap={onSwap ? (alt) => onSwap(line, alt) : undefined}
          />
        ))}
      </ul>
      <div className="receipt-rule my-3" />
      <dl className="space-y-1 text-sm">
        <div className="flex justify-between font-bold">
          <dt>{tp('results.total', sharedItems.length)}</dt>
          <dd className="font-mono">{price(store.shared_total)}</dd>
        </div>
        {hasExtras && (
          <div className="flex justify-between text-app-text-secondary">
            <dt>{t('results.everythingHere')}</dt>
            <dd className="font-mono">{price(store.full_total)}</dd>
          </div>
        )}
      </dl>
    </section>
  );
}
