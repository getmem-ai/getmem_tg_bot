// TypeScript interfaces for all API responses.

export type Tier = "free" | "premium" | string;
export type Role = "user" | "assistant";
export type Provider = "openrouter" | "openai" | "anthropic";

export interface ModelSpec {
  provider: Provider;
  id: string;
  label: string;
}

export interface User {
  id: number;
  username: string | null;
  first_name: string;
  tier: Tier;
  is_premium: boolean;
  premium_until: string | null;
  preferred_model: string | null;
  created_at: string;
}

export interface Usage {
  used_today: number;
  limit: number;
  remaining: number;
}

export interface Totals {
  messages: number;
  payments: number;
}

export interface TierInfo {
  key: string;
  name: string;
  daily_limit: number;
}

export interface MeResponse {
  user: User;
  usage: Usage;
  totals: Totals;
  is_admin: boolean;
  tier: TierInfo;
  available_models: ModelSpec[];
}

export interface SetModelResponse {
  preferred_model: string | null;
}

export interface ActivityItem {
  role: Role;
  content: string;
  model: string | null;
  created_at: string;
}

export interface ActivityResponse {
  items: ActivityItem[];
}

export interface UsagePoint {
  day: string;
  count: number;
}

export interface UsageSeriesResponse {
  series: UsagePoint[];
}

export interface RecentUser {
  id: number;
  first_name: string;
  username: string | null;
  tier: Tier;
  created_at: string;
}

export interface AdminStatsResponse {
  users: number;
  premium: number;
  messages_today: number;
  payments: number;
  recent_users: RecentUser[];
}

export interface HealthResponse {
  status: string;
}

export interface PromptResponse {
  system_prompt: string;
  is_default: boolean;
}

export interface RuntimeResponse {
  voice_enabled: boolean;
  disabled_models: string[];
  all_models: ModelSpec[];
}

export interface RuntimeUpdate {
  voice_enabled?: boolean;
  disabled_models?: string[];
}

export interface ProviderConfig {
  name: string;
  kind: Provider;
  is_default: boolean;
  enabled: boolean;
  has_key: boolean;
  key_masked: string | null;
  models: string[];
  note?: string | null;
}

export interface ProvidersResponse {
  providers: ProviderConfig[];
}

export interface ProviderUpdate {
  name: string;
  enabled?: boolean;
  api_key?: string;
  models?: string[];
}

export interface TierConfig {
  key: string;
  name: string;
  daily_limit: number;
  models: ModelSpec[];
}

export interface TiersResponse {
  tiers: TierConfig[];
}

export interface TierUpdate {
  key: string;
  daily_limit: number;
  models: Array<{ provider: Provider; id: string }>;
}
