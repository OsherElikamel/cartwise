import type { Alternative, BasketLine, ParsedItem, StoreBasket } from '../../types';
import { formatPrice } from '../../utils/format';
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
  const hasExtras = store.full_total !== store.shared_total;
  return (
    <section aria-label={`${store.chain_name} receipt`} className="rounded-2xl border border-app-border bg-app-surface p-4 md:p-5">
      <header className="mb-1 text-center">
        <p className="font-mono text-sm font-bold uppercase tracking-widest">{store.chain_name}</p>
        <p dir="auto" className="text-xs text-app-text-secondary">{store.store_name}</p>
      </header>
      <div className="receipt-rule my-3" />
      <ul className="divide-y divide-app-border">
        {store.lines.map((line) => (
          <BasketLineRow
            key={line.index}
            line={line}
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
      <dl className="space-y-1 font-mono text-sm">
        <div className="flex justify-between font-bold">
          <dt>Total ({sharedItems.length} shared item{sharedItems.length === 1 ? '' : 's'})</dt>
          <dd>{formatPrice(store.shared_total)}</dd>
        </div>
        {hasExtras && (
          <div className="flex justify-between text-app-text-secondary">
            <dt>Everything found here</dt>
            <dd>{formatPrice(store.full_total)}</dd>
          </div>
        )}
      </dl>
    </section>
  );
}
