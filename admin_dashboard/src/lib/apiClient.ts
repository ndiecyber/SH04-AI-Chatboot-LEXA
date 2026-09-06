const API_URL: string = window.__LEXA_CONFIG__?.apiUrl || window.location.origin;

declare global {
  interface Window {
    __LEXA_CONFIG__?: { apiUrl: string };
  }
}

interface RequestOptions extends Omit<RequestInit, 'method' | 'body'> {
  token?: string | null;
}

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public data?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

let isRefreshing = false;
let refreshPromise: Promise<string> | null = null;

async function refreshToken(): Promise<string> {
  const currentToken = localStorage.getItem('lexa_admin_token');
  if (!currentToken) throw new Error('No token');

  const res = await fetch(`${API_URL}/api/auth/refresh?token=${encodeURIComponent(currentToken)}`, {
    method: 'POST',
  });

  if (!res.ok) {
    localStorage.removeItem('lexa_admin_token');
    localStorage.removeItem('lexa_admin_user');
    window.location.href = '/login';
    throw new Error('Refresh failed');
  }

  const data = await res.json();
  localStorage.setItem('lexa_admin_token', data.token);
  return data.token;
}

async function request<T>(
  path: string,
  method: string,
  body?: unknown,
  options: RequestOptions = {},
  isRetry = false
): Promise<T> {
  const { token, ...fetchOptions } = options;

  const headers: Record<string, string> = {
    ...(fetchOptions.headers as Record<string, string> || {}),
  };

  if (body && !(body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: body instanceof FormData ? body : body ? JSON.stringify(body) : undefined,
    ...fetchOptions,
  });

  if (res.status === 401 && !isRetry && token) {
    try {
      if (!isRefreshing) {
        isRefreshing = true;
        refreshPromise = refreshToken();
      }
      const newToken = await refreshPromise!;
      isRefreshing = false;
      refreshPromise = null;
      return request<T>(path, method, body, { ...options, token: newToken }, true);
    } catch {
      isRefreshing = false;
      refreshPromise = null;
      throw new ApiError(401, 'Session expired. Please login again.');
    }
  }

  if (!res.ok) {
    let data: unknown;
    try {
      data = await res.json();
    } catch {}
    const msg = (data as { detail?: string })?.detail || `Request failed: ${res.status}`;
    throw new ApiError(res.status, msg, data);
  }

  return res.json() as Promise<T>;
}

export const api = {
  get<T>(path: string, options?: RequestOptions): Promise<T> {
    return request<T>(path, 'GET', undefined, options);
  },

  post<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return request<T>(path, 'POST', body, options);
  },

  put<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return request<T>(path, 'PUT', body, options);
  },

  delete<T>(path: string, options?: RequestOptions): Promise<T> {
    return request<T>(path, 'DELETE', undefined, options);
  },

  upload<T>(path: string, formData: FormData, options?: RequestOptions): Promise<T> {
    return request<T>(path, 'POST', formData, options);
  },

  getToken(): string | null {
    return localStorage.getItem('lexa_admin_token');
  },

  authGet<T>(path: string): Promise<T> {
    return this.get<T>(path, { token: this.getToken() });
  },

  authPost<T>(path: string, body?: unknown): Promise<T> {
    return this.post<T>(path, body, { token: this.getToken() });
  },

  authDelete<T>(path: string): Promise<T> {
    return this.delete<T>(path, { token: this.getToken() });
  },

  authUpload<T>(path: string, formData: FormData): Promise<T> {
    return this.upload<T>(path, formData, { token: this.getToken() });
  },
};

export { ApiError };
export default api;
