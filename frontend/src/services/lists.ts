import api from './api';
import type { BasketComparison, RunDetail, RunSummary, SavedList } from '../types';

export async function getLists(): Promise<SavedList[]> {
  const res = await api.get<SavedList[]>('/lists');
  return res.data;
}

export async function createList(name: string, text: string): Promise<SavedList> {
  const res = await api.post<SavedList>('/lists', { name, text });
  return res.data;
}

export async function updateList(id: string, patch: { name?: string; text?: string }): Promise<SavedList> {
  const res = await api.patch<SavedList>(`/lists/${id}`, patch);
  return res.data;
}

export async function deleteList(id: string): Promise<void> {
  await api.delete(`/lists/${id}`);
}

export async function compareSavedList(id: string): Promise<BasketComparison> {
  const res = await api.post<BasketComparison>(`/lists/${id}/compare`, undefined, { timeout: 90_000 });
  return res.data;
}

export async function getHistory(): Promise<RunSummary[]> {
  const res = await api.get<RunSummary[]>('/history');
  return res.data;
}

export async function getRun(id: string): Promise<RunDetail> {
  const res = await api.get<RunDetail>(`/history/${id}`);
  return res.data;
}
