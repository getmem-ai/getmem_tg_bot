// TypeScript interfaces for all API responses.

export type Tier = "free" | "premium" | string;
export type Role = "user" | "assistant";

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

export interface MeResponse {
  user: User;
  usage: Usage;
  totals: Totals;
  is_admin: boolean;
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
