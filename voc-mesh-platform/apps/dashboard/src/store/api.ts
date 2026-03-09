import { useTenantStore } from './tenant';

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const { token, tenant, logout } = useTenantStore.getState();
  const slug = tenant?.slug ?? '';

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  if (slug) {
    headers['X-Tenant-Slug'] = slug;
  }

  const res = await fetch(`/api/v1${path}`, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    logout();
    window.location.href = '/';
    throw new ApiError(401, 'Unauthorized');
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body.detail || `Request failed: ${res.status}`);
  }

  return res.json();
}

export interface SensorData {
  id: string;
  hardware_id: string;
  lat: number;
  lng: number;
  status: 'online' | 'offline' | 'maintenance';
  last_seen: string;
  type: string;
  parcela_id: string;
}

export interface Parcela {
  id: string;
  name: string;
  crop_type: string;
  area_km2: number;
  stress_index: number;
  bloom_index: number;
  pest_risk: number;
  carbon_flux: number;
  sensor_count: number;
  boundary_geojson: GeoJSON.Geometry | null;
}

export interface LiveData {
  timestamp: string;
  tvoc: number;
  voc: number;
  co: number;
  h2: number;
  ch4: number;
  o2: number;
  co2: number;
  ammonia: number;
  ethanol: number;
  temperature: number;
  humidity: number;
  soil_moisture: number;
  fire_alert: boolean;
}

export interface Prediction {
  id: string;
  parcela_id: string;
  created_at: string;
  prediction_for: string;
  confidence: number;
  stress_predicted: number;
  bloom_predicted: number;
  pest_predicted: number;
  thumbnail_url: string | null;
}

export interface Alert {
  id: string;
  parcela_id: string;
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  created_at: string;
  resolved: boolean;
}

export interface Insight {
  id: string;
  parcela_id: string;
  parcela_name: string;
  urgency: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  recommendation: string;
  scientific_reasoning: string;
  created_at: string;
}

export interface BillingInfo {
  current_month_estimate: number;
  currency: string;
  tier: string;
  sensors_count: number;
  area_km2: number;
  readings_count: number;
  api_calls: number;
  invoices: Array<{
    id: string;
    period: string;
    amount: number;
    status: 'paid' | 'pending' | 'overdue';
  }>;
}

export interface UsageStats {
  sensors: number;
  area_km2: number;
  readings_today: number;
  api_calls_today: number;
}

export const api = {
  getTenantConfig: () => apiFetch<{ tenant: Parcela[] }>('/tenant/config'),

  getSensors: () => apiFetch<SensorData[]>('/sensors'),

  getParcelas: () => apiFetch<Parcela[]>('/parcelas'),

  getParcelaLive: (parcelaId: string) =>
    apiFetch<LiveData>(`/parcelas/${parcelaId}/live`),

  getParcelaHistory: (parcelaId: string, hours: number) =>
    apiFetch<LiveData[]>(`/parcelas/${parcelaId}/history?hours=${hours}`),

  getPredictions: (parcelaId: string) =>
    apiFetch<Prediction[]>(`/parcelas/${parcelaId}/predictions`),

  getAlerts: (parcelaId?: string) =>
    apiFetch<Alert[]>(parcelaId ? `/alerts?parcela_id=${parcelaId}` : '/alerts'),

  getInsights: () => apiFetch<Insight[]>('/insights'),

  generateInsight: (parcelaId: string) =>
    apiFetch<Insight>(`/parcelas/${parcelaId}/insights/generate`, {
      method: 'POST',
    }),

  getBilling: () => apiFetch<BillingInfo>('/billing'),

  getUsage: () => apiFetch<UsageStats>('/usage'),
};
