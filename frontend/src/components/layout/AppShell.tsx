import { History, ListChecks, LogIn, LogOut, MapPin, ShoppingBasket } from 'lucide-react';
import type { ReactNode } from 'react';
import { Link, NavLink, Outlet } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import BrandMark from '../ui/BrandMark';
import ThemeToggle from '../ui/ThemeToggle';

const NAV = [
  { to: '/', label: 'Compare', icon: ShoppingBasket, end: true },
  { to: '/lists', label: 'Lists', icon: ListChecks, end: false },
  { to: '/history', label: 'History', icon: History, end: false },
  { to: '/branches', label: 'Branches', icon: MapPin, end: false },
];

function TopLink({ to, end, children }: { to: string; end: boolean; children: ReactNode }) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        `flex h-10 items-center gap-2 rounded-xl px-3 text-sm font-medium transition-colors ${
          isActive ? 'bg-app-elevated text-app-text' : 'text-app-text-secondary hover:bg-app-hover hover:text-app-text'
        }`
      }
    >
      {children}
    </NavLink>
  );
}

export default function AppShell() {
  const { user, logout } = useAuth();

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-40 border-b border-app-border bg-app-bg/90 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-5xl items-center gap-2 px-4 md:px-6">
          <Link to="/" aria-label="CartWise home" className="mr-2 flex items-center gap-2">
            <BrandMark />
            <span className="text-base font-bold tracking-tight">CartWise</span>
          </Link>

          {user && (
            <nav aria-label="Main" className="hidden items-center gap-1 md:flex">
              {NAV.map(({ to, label, icon: Icon, end }) => (
                <TopLink key={to} to={to} end={end}>
                  <Icon size={16} aria-hidden />
                  {label}
                </TopLink>
              ))}
            </nav>
          )}

          <div className="ml-auto flex items-center gap-1">
            <ThemeToggle />
            {user ? (
              <button
                type="button"
                onClick={logout}
                aria-label={`Sign out ${user.name}`}
                className="flex h-10 items-center gap-2 rounded-xl px-3 text-sm font-medium text-app-text-secondary hover:bg-app-hover hover:text-app-text"
              >
                <LogOut size={16} aria-hidden />
                <span className="hidden sm:inline">Sign out</span>
              </button>
            ) : (
              <Link
                to="/login"
                className="flex h-10 items-center gap-2 rounded-xl px-3 text-sm font-semibold text-accent hover:bg-app-hover"
              >
                <LogIn size={16} aria-hidden />
                Sign in
              </Link>
            )}
          </div>
        </div>
      </header>

      <main className={`mx-auto w-full max-w-5xl flex-1 px-4 py-6 md:px-6 md:py-8 ${user ? 'pb-28 md:pb-8' : ''}`}>
        <Outlet />
      </main>

      {user && (
        <nav
          aria-label="Main"
          className="fixed inset-x-0 bottom-0 z-40 grid grid-cols-4 border-t border-app-border bg-app-surface/95 pb-[env(safe-area-inset-bottom)] backdrop-blur md:hidden"
        >
          {NAV.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex h-16 flex-col items-center justify-center gap-1 text-xs font-medium ${
                  isActive ? 'text-accent' : 'text-app-text-secondary'
                }`
              }
            >
              <Icon size={20} aria-hidden />
              {label}
            </NavLink>
          ))}
        </nav>
      )}
    </div>
  );
}
