/** Клиент API. Контракт: docs/Tech/04-api-and-access.md. */

export type Role = 'user' | 'admin';

export interface Mod {
  slug: string;
  title: string;
  description: string;
  categories: string[];
  url: string;
}

export interface SearchResponse {
  mods: Mod[];
  /** null при непустом `mods` — LLM недоступна (RULE-ANS-04). */
  answer: string | null;
}

export class ApiError extends Error {
  constructor(public status: number) {
    super(`API ${status}`);
  }
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    credentials: 'same-origin',
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  });
  if (!res.ok) throw new ApiError(res.status);
  return res.status === 204 ? (undefined as T) : ((await res.json()) as T);
}

export const api = {
  me: () => request<{ role: Role }>('/api/auth/me').then((r) => r.role),
  login: (login: string, password: string) =>
    request<{ role: Role }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ login, password }),
    }).then((r) => r.role),
  logout: () => request<void>('/api/auth/logout', { method: 'POST' }),
  search: (query: string) =>
    request<SearchResponse>('/api/search', { method: 'POST', body: JSON.stringify({ query }) }),
  stats: () => request<{ requests: number }>('/api/admin/stats'),
};
