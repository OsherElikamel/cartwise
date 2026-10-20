import api from './api';
import type { User } from '../types';

export async function login(email: string, password: string): Promise<string> {
  const res = await api.post<{ access_token: string }>('/auth/login', { email, password });
  return res.data.access_token;
}

export async function register(name: string, email: string, password: string): Promise<User> {
  const res = await api.post<User>('/auth/register', { name, email, password });
  return res.data;
}

export async function getMe(token?: string): Promise<User> {
  const headers = token ? { Authorization: `Bearer ${token}` } : undefined;
  const res = await api.get<User>('/auth/me', { headers });
  return res.data;
}
