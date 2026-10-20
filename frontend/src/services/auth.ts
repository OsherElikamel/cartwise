import api from './api';
import type { User } from '../types';

export async function login(email: string, password: string): Promise<string> {
  const res = await api.post<{ access_token: string }>('/auth/login', { email, password });
  return res.data.access_token;
}

/** Creates the account and signs in, in one request: never a half-registered state. */
export async function register(name: string, email: string, password: string): Promise<{ access_token: string; user: User }> {
  const res = await api.post<{ access_token: string; user: User }>('/auth/register', { name, email, password });
  return res.data;
}

export async function getMe(token?: string): Promise<User> {
  const headers = token ? { Authorization: `Bearer ${token}` } : undefined;
  const res = await api.get<User>('/auth/me', { headers });
  return res.data;
}
