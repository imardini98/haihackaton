export class ApiError extends Error {
  status: number;
  payload: unknown;

  constructor(message: string, status: number, payload: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.payload = payload;
  }
}

function joinUrl(baseUrl: string, path: string): string {
  const base = baseUrl.replace(/\/+$/, '');
  const p = path.startsWith('/') ? path : `/${path}`;
  return `${base}${p}`;
}

function safeJsonParse(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

function errorMessageFromPayload(payload: unknown): string | null {
  if (!payload || typeof payload !== 'object') return null;
  // FastAPI commonly returns: { detail: "..." }
  const detail = (payload as { detail?: unknown }).detail;
  if (typeof detail === 'string' && detail.trim()) return detail;
  return null;
}

export function getApiBaseUrl(): string {
  const fromEnv = (import.meta.env.VITE_API_BASE_URL || '').trim();
  return fromEnv || 'http://localhost:8000';
}

export async function requestJson<TResponse>(
  path: string,
  init: RequestInit & { token?: string } = {}
): Promise<TResponse> {
  const url = joinUrl(getApiBaseUrl(), path);

  const headers = new Headers(init.headers);
  headers.set('Accept', 'application/json');
  if (!headers.has('Content-Type') && init.body != null) {
    headers.set('Content-Type', 'application/json');
  }
  if (init.token) {
    headers.set('Authorization', `Bearer ${init.token}`);
  }

  const res = await fetch(url, { ...init, headers });
  const text = await res.text();
  const payload = text ? safeJsonParse(text) : null;

  if (!res.ok) {
    const messageFromPayload = errorMessageFromPayload(payload);
    throw new ApiError(messageFromPayload || `Request failed (${res.status})`, res.status, payload);
  }

  return payload as TResponse;
}

