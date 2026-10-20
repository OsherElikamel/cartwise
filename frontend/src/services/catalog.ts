import api from './api';
import type { Chain, ProductResult, Store } from '../types';

export async function getChains(): Promise<Chain[]> {
  const res = await api.get<Chain[]>('/chains');
  return res.data;
}

export async function searchStores(search: string, chain?: string): Promise<Store[]> {
  const res = await api.get<Store[]>('/stores', { params: { search: search || undefined, chain, limit: 40 } });
  return res.data;
}

/** Free-text product search at one branch, for picking a product by hand. */
export async function searchProducts(q: string, storeId: string): Promise<ProductResult[]> {
  const res = await api.get<ProductResult[]>('/products/search', { params: { q, store_id: storeId, per_store: 12 } });
  return res.data;
}

/** The branches guests compare on (and signed-in users until they pick their own). */
export async function getDemoStores(): Promise<Store[]> {
  const res = await api.get<Store[]>('/stores', { params: { demo_only: true, tracked_only: true } });
  return res.data;
}
