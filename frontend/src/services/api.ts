import axios from 'axios';

export const TOKEN_KEY = 'cartwise_token';
export const RETURN_TO_KEY = 'cartwise_return_to';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    // Only an expired session redirects: a guest's request carries no token,
    // and a failed login attempt should show its own error in place.
    const sentToken = Boolean(err.config?.headers?.Authorization);
    const isLogin = err.config?.url?.includes('/auth/login');
    if (err.response?.status === 401 && sentToken && !isLogin) {
      localStorage.removeItem(TOKEN_KEY);
      if (window.location.pathname !== '/login') {
        sessionStorage.setItem(RETURN_TO_KEY, window.location.pathname + window.location.search);
        window.location.href = '/login?expired=1';
      }
    }
    return Promise.reject(err);
  },
);

export default api;
