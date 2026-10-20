import { History, ListChecks, LogIn, LogOut, MapPin, ShoppingBasket } from 'lucide-react';
import { Link, NavLink, Outlet } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import type { MessageKey } from '../../i18n/en';
import { useI18n } from '../../i18n/LanguageContext';
import BrandMark from '../ui/BrandMark';
import LanguageToggle from '../ui/LanguageToggle';
import ThemeToggle from '../ui/ThemeToggle';

const NAV: { to: string; label: MessageKey; icon: typeof ShoppingBasket; end: boolean }[] = [
  { to: '/', label: 'nav.compare', icon: ShoppingBasket, end: true },
  { to: '/lists', label: 'nav.lists', icon: ListChecks, end: false },
  { to: '/history', label: 'nav.history', icon: History, end: false },
  { to: '/branches', label: 'nav.branches', icon: MapPin, end: false },
];

export default function AppShell() {
  const { user, logout } = useAuth();
  const { t } = useI18n();

  return (
    <div className={`relative min-h-screen px-2 pt-2 md:px-8 md:pb-10 md:pt-20 ${user ? 'pb-24' : 'pb-2'}`}>
      <div className="aurora-frame" aria-hidden><div className="aurora" /></div>

      <div className="window mx-auto flex min-h-[calc(100vh-1rem)] max-w-6xl flex-col rounded-3xl md:min-h-[calc(100vh-7rem)] md:rounded-[2rem]">
        <header className="flex h-16 min-w-0 items-center gap-1 px-3 md:h-20 md:gap-2 md:px-8">
          <Link to="/" aria-label={t('nav.home')} className="me-2 flex items-center gap-2.5">
            <BrandMark />
            <span className="hidden text-lg font-bold tracking-tight sm:inline">CartWise</span>
          </Link>

          {user && (
            <nav aria-label={t('nav.main')} className="mx-auto hidden items-center gap-1 md:flex">
              {NAV.map(({ to, label, icon: Icon, end }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={end}
                  className={({ isActive }) =>
                    `flex h-10 items-center gap-2 rounded-full px-4 text-sm font-medium transition-colors ${
                      isActive ? 'bg-app-text text-app-bg' : 'text-app-text-secondary hover:bg-app-hover hover:text-app-text'
                    }`
                  }
                >
                  <Icon size={16} aria-hidden />
                  {t(label)}
                </NavLink>
              ))}
            </nav>
          )}

          <div className="ms-auto flex items-center gap-1">
            <LanguageToggle />
            <ThemeToggle />
            {user ? (
              <button
                type="button"
                onClick={logout}
                aria-label={t('nav.signOutUser', { name: user.name })}
                className="flex h-10 items-center gap-2 rounded-full px-3 text-sm font-medium text-app-text-secondary hover:bg-app-hover hover:text-app-text"
              >
                <LogOut size={16} className="rtl:rotate-180" aria-hidden />
                <span className="hidden sm:inline">{t('nav.signOut')}</span>
              </button>
            ) : (
              <Link
                to="/login"
                className="ms-1 flex h-10 shrink-0 items-center gap-2 rounded-full bg-accent px-4 text-sm font-semibold text-on-accent hover:bg-accent-hover"
              >
                <LogIn size={16} className="rtl:rotate-180" aria-hidden />
                {t('nav.signIn')}
              </Link>
            )}
          </div>
        </header>

        <main className="w-full flex-1 px-4 pb-8 pt-2 md:px-12 md:pb-12">
          <div className="mx-auto max-w-4xl">
            <Outlet />
          </div>
        </main>
      </div>

      {user && (
        <nav
          aria-label={t('nav.main')}
          className="window fixed inset-x-2 bottom-2 z-40 grid grid-cols-4 rounded-2xl pb-[env(safe-area-inset-bottom)] md:hidden"
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
              {t(label)}
            </NavLink>
          ))}
        </nav>
      )}
    </div>
  );
}
