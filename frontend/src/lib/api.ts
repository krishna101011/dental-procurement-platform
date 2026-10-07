const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1';

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('token');
  const headers = new Headers(options.headers);
  if (!headers.has('Content-Type') && options.body && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  if (token) headers.set('Authorization', `Bearer ${token}`);

  const res = await fetch(API + path, { ...options, headers });
  if (res.status === 204) return undefined as T;

  const payload = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new ApiError(payload.detail || 'Request failed', res.status);
  }
  return payload as T;
}

export function assetUrl(path?: string | null) {
  if (!path) return `${API.replace('/api/v1', '')}/product-images/generic.svg`;
  if (path.startsWith('http')) return path;
  return `${API.replace('/api/v1', '')}${path}`;
}
