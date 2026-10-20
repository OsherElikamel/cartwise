import type { BasketComparison, Confidence, Pick } from '../types';

/** Every current product pick, with one line optionally replaced. */
export function toPicks(
  result: BasketComparison,
  replace?: { storeId: string; index: number; itemCode: string; confidence: Confidence },
): Pick[] {
  const picks: Pick[] = [];
  for (const store of result.stores) {
    for (const line of store.lines) {
      const isReplaced = replace && replace.storeId === store.store_id && replace.index === line.index;
      if (isReplaced) {
        picks.push({ store_id: store.store_id, index: line.index, item_code: replace.itemCode, confidence: replace.confidence, reason: 'You chose this' });
      } else if (line.item_code && line.confidence) {
        picks.push({ store_id: store.store_id, index: line.index, item_code: line.item_code, confidence: line.confidence, reason: line.reason ?? '' });
      }
    }
  }
  return picks;
}

/** Mark one line as the user's saved choice; prices are unchanged by a confirm. */
export function markRemembered(result: BasketComparison, storeId: string, index: number): BasketComparison {
  return {
    ...result,
    stores: result.stores.map((store) =>
      store.store_id !== storeId
        ? store
        : { ...store, lines: store.lines.map((l) => (l.index === index ? { ...l, confidence: 'remembered', reason: 'Your saved choice' } : l)) },
    ),
  };
}
