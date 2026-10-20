import api from './api';
import type { Store } from '../types';

export async function getMyStores(): Promise<Store[]> {
  const res = await api.get<Store[]>('/me/stores');
  return res.data;
}

/** Resolves once following is saved; the branch may still be loading prices. */
export async function followStore(storeId: string): Promise<Store> {
  const res = await api.post<Store>('/me/stores', { store_id: storeId });
  return res.data;
}

export async function unfollowStore(storeId: string): Promise<void> {
  await api.delete(`/me/stores/${storeId}`);
}
