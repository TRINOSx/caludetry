import { Navigate } from 'react-router-dom';
import { useTenantStore } from '../store/tenant';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const token = useTenantStore((s) => s.token);
  const tenant = useTenantStore((s) => s.tenant);

  if (!token || !tenant) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}
