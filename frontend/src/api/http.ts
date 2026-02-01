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
  // #region agent log
  fetch('http://127.0.0.1:7242/ingest/0e77b2eb-a7f1-4359-ad19-ef751822d1d5',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'frontend/src/api/http.ts:getApiBaseUrl',message:'Computed API base URL',data:{hasEnvValue:Boolean(fromEnv),baseUrl:(fromEnv||'http://localhost:8000')},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'H4'})}).catch(()=>{});
  // #endregion
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

  // #region agent log
  fetch('http://127.0.0.1:7242/ingest/0e77b2eb-a7f1-4359-ad19-ef751822d1d5',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'frontend/src/api/http.ts:requestJson',message:'HTTP request start',data:{path,method:(init.method||'GET'),url,hasAuthHeader:Boolean(init.token),hasBody:Boolean(init.body)},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'H1'})}).catch(()=>{});
  // #endregion

  const res = await fetch(url, { ...init, headers });
  const text = await res.text();
  const payload = text ? safeJsonParse(text) : null;

  // #region agent log
  fetch('http://127.0.0.1:7242/ingest/0e77b2eb-a7f1-4359-ad19-ef751822d1d5',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'frontend/src/api/http.ts:requestJson',message:'HTTP response received',data:{path,method:(init.method||'GET'),status:res.status,ok:res.ok,contentType:(res.headers.get('content-type')||null),payloadType:(payload===null?'null':Array.isArray(payload)?'array':typeof payload)},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'H2'})}).catch(()=>{});
  // #endregion

  if (!res.ok) {
    const messageFromPayload = errorMessageFromPayload(payload);
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/0e77b2eb-a7f1-4359-ad19-ef751822d1d5',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'frontend/src/api/http.ts:requestJson',message:'HTTP error thrown',data:{path,method:(init.method||'GET'),status:res.status,hasDetailMessage:Boolean(messageFromPayload)},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'H3'})}).catch(()=>{});
    // #endregion
    throw new ApiError(messageFromPayload || `Request failed (${res.status})`, res.status, payload);
  }

  return payload as TResponse;
}

