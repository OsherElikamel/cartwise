import api from './api';
import type { BasketComparison, ParsedItem, Pick } from '../types';

export async function compareList(text: string, storeIds?: string[]): Promise<BasketComparison> {
  const res = await api.post<BasketComparison>('/baskets/compare', { text, store_ids: storeIds });
  return res.data;
}

/** Recalculate totals for explicit picks after a confirm or swap. No AI calls. */
export async function reprice(items: ParsedItem[], storeIds: string[], picks: Pick[]): Promise<BasketComparison> {
  const res = await api.post<BasketComparison>('/baskets/reprice', { items, store_ids: storeIds, picks });
  return res.data;
}
