import { useState, useEffect } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import clsx from 'clsx';
import Sidebar from './Sidebar';
import { useTenantStore } from '../store/tenant';
import { api, type Alert, type Parcela } from '../store/api';

export default function Layout() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [parcelas, setParcelas] = useState<Parcela[]>([]);
  const [selectedParcela, setSelectedParcela] = useState<string>('');
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const tenant = useTenantStore((s) => s.tenant);
  const logout = useTenantStore((s) => s.logout);
  const navigate = useNavigate();

  const activeAlerts = alerts.filter((a) => !a.resolved);

  useEffect(() => {
    api.getParcelas().then(setParcelas).catch(() => {});
    api.getAlerts().then(setAlerts).catch(() => {});

    const interval = setInterval(() => {
      api.getAlerts().then(setAlerts).catch(() => {});
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="flex h-screen overflow-hidden bg-space">
      {/* Mobile overlay */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-30 lg:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar - desktop */}
      <div className="hidden lg:block">
        <Sidebar
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        />
      </div>

      {/* Sidebar - mobile */}
      <div
        className={clsx(
          'fixed inset-y-0 left-0 z-40 lg:hidden transition-transform duration-300',
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        <Sidebar
          collapsed={false}
          onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
          onClose={() => setMobileMenuOpen(false)}
        />
      </div>

      {/* Main area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="h-14 bg-space-100/80 backdrop-blur-sm border-b border-white/5 flex items-center justify-between px-4 gap-4 flex-shrink-0">
          <div className="flex items-center gap-3">
            {/* Mobile hamburger */}
            <button
              className="lg:hidden p-1.5 text-text-muted hover:text-text"
              onClick={() => setMobileMenuOpen(true)}
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
              </svg>
            </button>

            {/* Parcela selector */}
            <select
              value={selectedParcela}
              onChange={(e) => {
                setSelectedParcela(e.target.value);
                if (e.target.value) {
                  navigate(`/parcela/${e.target.value}`);
                }
              }}
              className="bg-space-50 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-text font-body focus:outline-none focus:border-voc/50 max-w-[200px]"
            >
              <option value="">All Parcelas</option>
              {parcelas.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-4">
            {/* Alert badge */}
            <button
              onClick={() => navigate('/dashboard')}
              className="relative p-2 text-text-muted hover:text-text transition-colors"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0" />
              </svg>
              {activeAlerts.length > 0 && (
                <span className={clsx(
                  'absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] rounded-full bg-alert text-white text-[10px] font-bold flex items-center justify-center px-1',
                  activeAlerts.some((a) => a.severity === 'critical') && 'animate-pulse-fast',
                )}>
                  {activeAlerts.length}
                </span>
              )}
            </button>

            {/* Tenant info */}
            <div className="hidden sm:flex items-center gap-2">
              <div className="w-7 h-7 rounded-full bg-voc/20 flex items-center justify-center">
                <span className="text-voc text-xs font-bold">
                  {tenant?.name?.[0]?.toUpperCase() ?? 'T'}
                </span>
              </div>
              <span className="text-sm text-text-muted font-body">{tenant?.name}</span>
            </div>

            {/* Logout */}
            <button
              onClick={handleLogout}
              className="text-text-dim hover:text-alert text-sm transition-colors"
              title="Logout"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0 0 13.5 3h-6a2.25 2.25 0 0 0-2.25 2.25v13.5A2.25 2.25 0 0 0 7.5 21h6a2.25 2.25 0 0 0 2.25-2.25V15m3 0 3-3m0 0-3-3m3 3H9" />
              </svg>
            </button>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-auto p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
