import { lazy, Suspense } from 'react';
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
  if (isLoading) return <PageFallback />;
  if (!user) {
    sessionStorage.setItem(RETURN_TO_KEY, location.pathname + location.search);
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}

function GuestRoute() {
  const { user, isLoading } = useAuth();
  if (isLoading) return <PageFallback />;
  return user ? <Navigate to="/" replace /> : <Outlet />;
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
