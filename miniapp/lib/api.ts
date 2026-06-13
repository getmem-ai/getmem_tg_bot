// Typed fetch client that injects the `Authorization: tma <initData>` header
// and throws typed errors. The frontend never validates the signature itself.

import { getInitData } from "./telegram";
import type {
  ActivityResponse,
  AdminStatsResponse,
  AdminUser,
  AdminUsersResponse,
  AdminUserUpdate,
  AnalyticsResponse,
  BroadcastResponse,
  HealthResponse,
  InvoiceResponse,
  MeResponse,
  PromptResponse,
  ProvidersResponse,
  ProviderConfig,
  ProviderUpdate,
  RuntimeResponse,
  RuntimeUpdate,
  SetModelResponse,
  SetRoleResponse,
  TiersResponse,
  TierUpdate,
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

function putJson<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export const api = {
  // ---- User ----
  me: () => request<MeResponse>("/me"),
  setModel: (model: string | null) =>
    putJson<SetModelResponse>("/me/model", { model }),
  setRole: (update: { role?: string | null; enabled?: boolean }) =>
    putJson<SetRoleResponse>("/me/role", update),
  createInvoice: (tier_key: string) =>
    request<InvoiceResponse>("/me/invoice", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tier_key }),
    }),
  activity: (limit = 20) =>
    request<ActivityResponse>(`/me/activity?limit=${encodeURIComponent(limit)}`),
  usage: (days = 14) =>
    request<UsageSeriesResponse>(`/me/usage?days=${encodeURIComponent(days)}`),

  // ---- Admin: stats & prompt ----
  adminStats: () => request<AdminStatsResponse>("/admin/stats"),
  getPrompt: () => request<PromptResponse>("/admin/prompt"),
  setPrompt: (system_prompt: string) =>
    putJson<PromptResponse>("/admin/prompt", { system_prompt }),

  // ---- Admin: runtime (voice + disabled models) ----
  getRuntime: () => request<RuntimeResponse>("/admin/runtime"),
  setRuntime: (update: RuntimeUpdate) =>
    putJson<RuntimeResponse>("/admin/runtime", update),

  // ---- Admin: providers ----
  getProviders: () => request<ProvidersResponse>("/admin/providers"),
  setProvider: (update: ProviderUpdate) =>
    putJson<ProviderConfig>("/admin/providers", update),

  // ---- Admin: users ----
  adminListUsers: (params?: { search?: string; limit?: number; offset?: number }) => {
    const qs = new URLSearchParams();
    if (params?.search) qs.set("search", params.search);
    if (params?.limit != null) qs.set("limit", String(params.limit));
    if (params?.offset != null) qs.set("offset", String(params.offset));
    const query = qs.toString();
    return request<AdminUsersResponse>(`/admin/users${query ? `?${query}` : ""}`);
  },
  adminUpdateUser: (id: number, update: AdminUserUpdate) =>
    putJson<AdminUser>(`/admin/users/${id}`, update),

  // ---- Admin: tiers ----
  getTiers: () => request<TiersResponse>("/admin/tiers"),
  setTiers: (tiers: TierUpdate[]) =>
    putJson<TiersResponse>("/admin/tiers", { tiers }),

  // ---- Admin: analytics & broadcast ----
  getAnalytics: (days = 14) =>
    request<AnalyticsResponse>(`/admin/analytics?days=${encodeURIComponent(days)}`),
  broadcast: (text: string, tier?: string | null) =>
    request<BroadcastResponse>("/admin/broadcast", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, tier: tier ?? null }),
    }),

  health: () => request<HealthResponse>("/health"),
};
