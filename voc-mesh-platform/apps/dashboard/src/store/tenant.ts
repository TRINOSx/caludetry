import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface Tenant {
  id: string;
  slug: string;
  name: string;
  tier: 'free' | 'pro' | 'enterprise';
  feature_flags: Record<string, boolean>;
}

interface TenantState {
  tenant: Tenant | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;
  login: (slug: string, credentials: { username: string; password: string }) => Promise<void>;
  logout: () => void;
  setTenant: (tenant: Tenant) => void;
  setToken: (token: string) => void;
}

export const useTenantStore = create<TenantState>()(
  persist(
    (set) => ({
      tenant: null,
      token: null,
      isLoading: false,
      error: null,

      login: async (slug, credentials) => {
        set({ isLoading: true, error: null });
        try {
          const res = await fetch(`/api/v1/tenants/${slug}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(credentials),
          });

          if (!res.ok) {
            const body = await res.json().catch(() => ({}));
            throw new Error(body.detail || 'Login failed');
          }

          const data = await res.json();
          set({
            token: data.access_token,
            tenant: data.tenant,
            isLoading: false,
            error: null,
          });
        } catch (err) {
          set({
            isLoading: false,
            error: err instanceof Error ? err.message : 'Login failed',
          });
          throw err;
        }
      },

      logout: () => {
        set({ tenant: null, token: null, error: null });
      },

      setTenant: (tenant) => set({ tenant }),
      setToken: (token) => set({ token }),
    }),
    {
      name: 'voc-mesh-auth',
      partialize: (state) => ({
        tenant: state.tenant,
        token: state.token,
      }),
    },
  ),
);

export function useFeatureFlag(flagName: string): boolean {
  const tenant = useTenantStore((s) => s.tenant);
  if (!tenant) return false;
  return tenant.feature_flags[flagName] ?? false;
}
