import api from './api';
import type { ChainBranches, Locality } from '../types';

export async function searchLocalities(search: string): Promise<Locality[]> {
  const res = await api.get<Locality[]>('/localities', { params: { search, limit: 8 } });
  return res.data;
}

export async function getLocality(code: string): Promise<Locality> {
  const res = await api.get<Locality>(`/localities/${code}`);
  return res.data;
}

/** Per chain: branches in the city, or the nearest cities that have one. */
export async function getBranchesNear(code: string, chain?: string): Promise<ChainBranches[]> {
  const res = await api.get<ChainBranches[]>(`/localities/${code}/branches`, { params: { chain } });
  return res.data;
}

export async function setHomeLocality(code: string | null): Promise<void> {
  await api.patch('/me/home', { home_locality_code: code });
}
