import { API_BASE_URL } from "../constants";

const AUTH_TOKEN_STORAGE_KEY = "ethos-auth-token";

let pendingToken: Promise<string> | null = null;

function loadToken(): string {
  return window.localStorage.getItem(AUTH_TOKEN_STORAGE_KEY) ?? "";
}

function saveToken(token: string): void {
  window.localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, token);
}

export async function ensureAuthToken(): Promise<string> {
  const existing = loadToken();
  if (existing) return existing;

  if (!pendingToken) {
    pendingToken = fetch(`${API_BASE_URL}/auth/guest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`Authentication failed (${response.status})`);
        }
        const payload = (await response.json()) as { access_token?: string };
        const token = payload.access_token?.trim() ?? "";
        if (!token) {
          throw new Error("Authentication token missing");
        }
        saveToken(token);
        return token;
      })
      .finally(() => {
        pendingToken = null;
      });
  }

  return pendingToken;
}

export async function authFetch(input: RequestInfo | URL, init: RequestInit = {}) {
  const token = await ensureAuthToken();
  const headers = new Headers(init.headers ?? {});
  headers.set("Authorization", `Bearer ${token}`);
  return fetch(input, { ...init, headers });
}
