import { lazy, Suspense, useEffect } from 'react';
import { Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom';
import AppShell from '../components/layout/AppShell';
import Skeleton from '../components/ui/Skeleton';
import { useAuth } from '../contexts/AuthContext';
import { RETURN_TO_KEY } from '../services/api';

const ComparePage = lazy(() => import('../pages/ComparePage'));
const LoginPage = lazy(() => import('../pages/LoginPage'));
const RegisterPage = lazy(() => import('../pages/RegisterPage'));
const BranchesPage = lazy(() => import('../pages/BranchesPage'));
const ListsPage = lazy(() => import('../pages/ListsPage'));
const HistoryPage = lazy(() => import('../pages/HistoryPage'));
const HistoryDetailPage = lazy(() => import('../pages/HistoryDetailPage'));
const NotFoundPage = lazy(() => import('../pages/NotFoundPage'));

function PageFallback() {
  return <div className="space-y-4"><Skeleton className="h-10 w-2/3" /><Skeleton className="h-48" /></div>;
}

function ProtectedRoute() {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  // Arrived where sign-in was meant to return to: forget the saved path.
  useEffect(() => {
    if (user && sessionStorage.getItem(RETURN_TO_KEY) === location.pathname + location.search) {
      sessionStorage.removeItem(RETURN_TO_KEY);
    }
  }, [user, location]);

  if (isLoading) return <PageFallback />;
  if (!user) {
    sessionStorage.setItem(RETURN_TO_KEY, location.pathname + location.search);
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}

/** Sign-in and sign-up pages. This route alone decides where a signed-in user
 *  goes next: new accounts to pick their branches, returning users back to where
 *  they were. (When the pages also navigated, the two raced and "home" won,
 *  dropping new users on the home page.) */
function GuestRoute() {
  const { user, isLoading } = useAuth();
  const location = useLocation();
  if (isLoading) return <PageFallback />;
  if (user) {
    const target = location.pathname === '/register' ? '/branches' : sessionStorage.getItem(RETURN_TO_KEY) ?? '/';
    return <Navigate to={target} replace />;
  }
  return <Outlet />;
}

export default function AppRoutes() {
  return (
    <Suspense fallback={<PageFallback />}>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<ComparePage />} />
          <Route element={<GuestRoute />}>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
          </Route>
          <Route element={<ProtectedRoute />}>
            <Route path="/branches" element={<BranchesPage />} />
            <Route path="/lists" element={<ListsPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/history/:id" element={<HistoryDetailPage />} />
          </Route>
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
