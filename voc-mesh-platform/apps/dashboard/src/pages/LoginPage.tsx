import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTenantStore } from '../store/tenant';

export default function LoginPage() {
  const [slug, setSlug] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const { login, isLoading, error } = useTenantStore();
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      await login(slug, { username, password });
      navigate('/dashboard');
    } catch {
      // error is set in store
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-space p-4">
      {/* Background glow */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-voc/5 rounded-full blur-[120px]" />
      </div>

      <div className="w-full max-w-md relative">
        {/* Branding */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-voc/10 border border-voc/20 mb-4 voc-glow">
            <span className="text-voc font-display font-bold text-2xl">V</span>
          </div>
          <h1 className="font-display font-bold text-2xl text-text">
            VOC <span className="text-voc">Mesh</span>
          </h1>
          <p className="text-text-muted text-sm mt-1 font-body">
            Agricultural VOC Monitoring Platform
          </p>
        </div>

        {/* Login card */}
        <div className="glass-panel p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-body text-text-muted mb-1.5">
                Tenant Slug
              </label>
              <input
                type="text"
                value={slug}
                onChange={(e) => setSlug(e.target.value)}
                placeholder="my-farm"
                required
                className="w-full bg-space border border-white/10 rounded-lg px-3 py-2.5 text-sm text-text font-body placeholder:text-text-dim focus:outline-none focus:border-voc/50 transition-colors"
              />
            </div>

            <div>
              <label className="block text-sm font-body text-text-muted mb-1.5">
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="admin"
                required
                className="w-full bg-space border border-white/10 rounded-lg px-3 py-2.5 text-sm text-text font-body placeholder:text-text-dim focus:outline-none focus:border-voc/50 transition-colors"
              />
            </div>

            <div>
              <label className="block text-sm font-body text-text-muted mb-1.5">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="w-full bg-space border border-white/10 rounded-lg px-3 py-2.5 text-sm text-text font-body placeholder:text-text-dim focus:outline-none focus:border-voc/50 transition-colors"
              />
            </div>

            {error && (
              <div className="bg-alert/10 border border-alert/20 rounded-lg px-3 py-2 text-alert text-sm font-body">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-voc hover:bg-voc-dark text-space font-body font-semibold py-2.5 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm"
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Signing in...
                </span>
              ) : (
                'Sign In'
              )}
            </button>
          </form>
        </div>

        <p className="text-center text-text-dim text-xs mt-6 font-body">
          Multi-tenant SaaS Platform for Agricultural VOC Monitoring
        </p>
      </div>
    </div>
  );
}
