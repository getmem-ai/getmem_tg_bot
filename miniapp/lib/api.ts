// Typed fetch client that injects the `Authorization: tma <initData>` header
// and throws typed errors. The frontend never validates the signature itself.

import { getInitData } from "./telegram";
import type {
  ActivityResponse,
  AdminStatsResponse,
  HealthResponse,
  MeResponse,
  PromptResponse,
  UsageSeriesResponse,
} from "./types";

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "/api";

export class ApiError extends Error {
  readonly status: number;
  readonly body: string;

  constructor(status: number, message: string, body: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }

  /** Backend signals the user is not an admin. */
  get isForbidden(): boolean {
    return this.status === 403;
  }

  get isUnauthorized(): boolean {
    return this.status === 401;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const initData = getInitData();

  const headers = new Headers(init?.headers);
  headers.set("Accept", "application/json");
  if (initData) {
    headers.set("Authorization", `tma ${initData}`);
  }

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers,
      cache: "no-store",
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Network request failed";
    throw new ApiError(0, message, "");
  }

  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new ApiError(res.status, `Request to ${path} failed (${res.status})`, body);
  }

  if (res.status === 204) {
    return undefined as T;
  }

  return (await res.json()) as T;
}

export const api = {
  me: () => request<MeResponse>("/me"),
  activity: (limit = 20) =>
    request<ActivityResponse>(`/me/activity?limit=${encodeURIComponent(limit)}`),
  usage: (days = 14) =>
    request<UsageSeriesResponse>(`/me/usage?days=${encodeURIComponent(days)}`),
  adminStats: () => request<AdminStatsResponse>("/admin/stats"),
  getPrompt: () => request<PromptResponse>("/admin/prompt"),
  setPrompt: (system_prompt: string) =>
    request<PromptResponse>("/admin/prompt", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ system_prompt }),
    }),
  health: () => request<HealthResponse>("/health"),
};
