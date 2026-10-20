import { useState } from 'react';
import { useToast } from '../contexts/ToastContext';
import { reprice } from '../services/baskets';
import { saveChoice } from '../services/matches';
import type { Alternative, BasketComparison, BasketLine, StoreBasket } from '../types';
import { markRemembered, toPicks } from '../utils/basket';
import { getErrorMessage } from '../utils/errors';

/** Confirm and swap for a basket on screen. Prices always come back from the server. */
export function useBasketEditing(canSave: boolean) {
  const [result, setResult] = useState<BasketComparison | null>(null);
  const [busyLine, setBusyLine] = useState<string | null>(null);
  const { showSuccess, showError } = useToast();

  const confirm = async (store: StoreBasket, line: BasketLine) => {
    if (!result || !line.item_code) return;
    setBusyLine(`${store.store_id}:${line.index}`);
    try {
      await saveChoice(line.match_key, store.store_id, line.item_code);
      setResult((r) => (r ? markRemembered(r, store.store_id, line.index) : r));
      showSuccess(`Saved. ${store.chain_name} will use this product next time.`);
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setBusyLine(null);
    }
  };

  const swap = async (store: StoreBasket, line: BasketLine, alt: Alternative) => {
    if (!result) return;
    setBusyLine(`${store.store_id}:${line.index}`);
    try {
      if (canSave) await saveChoice(line.match_key, store.store_id, alt.item_code);
      const picks = toPicks(result, {
        storeId: store.store_id, index: line.index, itemCode: alt.item_code,
        confidence: canSave ? 'remembered' : 'high',
      });
      setResult(await reprice(result.items, result.stores.map((s) => s.store_id), picks));
      showSuccess(canSave ? 'Swapped and saved for next time.' : 'Swapped. Sign in to keep your choices.');
    } catch (err) {
      showError(getErrorMessage(err));
    } finally {
      setBusyLine(null);
    }
  };

  return { result, setResult, busyLine, confirm, swap };
}
