import api from './api';

/** Remember this product for this list item at this branch's chain. */
export async function saveChoice(matchKey: string, storeId: string, itemCode: string): Promise<void> {
  await api.put('/matches', { match_key: matchKey, store_id: storeId, item_code: itemCode });
}
