import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { TOKEN_KEY } from '../services/api';
import { getMe, login as loginRequest, register as registerRequest } from '../services/auth';
import type { User } from '../types';

interface AuthState {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(() => Boolean(localStorage.getItem(TOKEN_KEY)));

  useEffect(() => {
    if (!localStorage.getItem(TOKEN_KEY)) return;
    getMe()
      .then(setUser)
      .catch(() => localStorage.removeItem(TOKEN_KEY))
      .finally(() => setIsLoading(false));
  }, []);

  const login = async (email: string, password: string) => {
    const token = await loginRequest(email, password);
    const me = await getMe(token);
    localStorage.setItem(TOKEN_KEY, token);
    setUser(me);
  };

  const register = async (name: string, email: string, password: string) => {
    const { access_token, user: created } = await registerRequest(name, email, password);
    localStorage.setItem(TOKEN_KEY, access_token);
    setUser(created);
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>{children}</AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
