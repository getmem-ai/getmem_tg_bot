// TypeScript interfaces for all API responses.

export type Tier = "free" | "premium" | string;
export type Role = "user" | "assistant";
export type Provider = "openrouter" | "openai" | "anthropic";

export interface ModelSpec {
  provider: Provider;
  id: string;
  label: string;
}

export interface Brand {
  name: string;
  tagline: string;
}

export interface User {
  id: number;
  username: string | null;
  first_name: string;
  tier: Tier;
  is_premium: boolean;
  premium_until: string | null;
  preferred_model: string | null;
  role: string | null;
  role_enabled: boolean;
  avatar: string | null;
  reply_language: string | null;
  reply_style: string | null;
  reply_length: string | null;
  timezone: string;
  created_at: string;
}

export interface ProfileUpdate {
  avatar?: string | null;
  reply_language?: string | null;
  reply_style?: string | null;
  reply_length?: string | null;
  timezone?: string;
}

export interface ProfileResponse {
  avatar: string | null;
  reply_language: string | null;
  reply_style: string | null;
  reply_length: string | null;
  timezone: string;
}

export type ScheduleFrequency =
  | "daily"
  | "weekly"
  | "interval"
  | "as_needed"
  | string;

export interface ScheduledTask {
  id: number;
  title: string;
  prompt: string;
  frequency: ScheduleFrequency;
  times: string[]; // ["08:00", "20:00"]
  weekdays: number[]; // 0=Mon … 6=Sun
  interval_days: number | null; // used when frequency === "interval"
  enabled: boolean;
  next_run_at: string | null;
  last_run_at: string | null;
  created_at: string;
}

export interface ScheduleInput {
  title: string;
  prompt: string;
  frequency: ScheduleFrequency;
  times: string[];
  weekdays: number[];
  interval_days?: number | null;
  enabled: boolean;
}

export interface SchedulesResponse {
  tasks: ScheduledTask[];
  timezone: string;
  enabled: boolean; // operator allows scheduling at all
}

export interface ScheduleRun {
  id: number;
  task_id: number;
  fired_at: string;
  status: string;
  preview: string;
}

export interface ScheduleRunsResponse {
  runs: ScheduleRun[];
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

export interface UpgradeTier {
  key: string;
  name: string;
  daily_limit: number;
  price_stars: number;
  period_days: number;
  model_count: number;
  models: ModelSpec[];
}

export interface MeResponse {
  user: User;
  usage: Usage;
  totals: Totals;
  is_admin: boolean;
  tier: TierInfo;
  available_models: ModelSpec[];
  upgrade_tiers: UpgradeTier[];
  user_roles_enabled: boolean;
  brand: Brand;
}

export interface SetModelResponse {
  preferred_model: string | null;
}

export interface SetRoleResponse {
  role: string | null;
  enabled: boolean;
}

export interface InvoiceResponse {
  invoice_link: string;
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

export interface AdminUser {
  id: number;
  first_name: string | null;
  username: string | null;
  tier: string;
  is_premium: boolean;
  premium_until: string | null;
  banned: boolean;
  is_admin: boolean;
  env_admin: boolean; // admin via env ADMIN_IDS — can't be revoked in the UI
  limit_override: number | null;
  used_today: number;
  daily_limit: number;
  messages: number;
  payments: number;
  created_at: string;
}

export interface AdminUsersResponse {
  users: AdminUser[];
  total: number;
  limit: number;
  offset: number;
}

export interface AdminUserUpdate {
  banned?: boolean;
  is_admin?: boolean; // grant/revoke admin rights
  limit_override?: number | null; // null clears the override
  tier?: string; // tier key; "free" downgrades; paid key grants for its period
  reset_usage?: boolean; // true → reset today's counter
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
  user_roles_enabled: boolean;
  generation_paused: boolean;
  max_tokens: number;
  vision_enabled: boolean;
  vision_model: string;
  vision_provider: string;
  vision_premium_only: boolean;
  welcome_message: string;
  brand_name: string;
  brand_tagline: string;
  streaming_enabled: boolean;
  scheduling_enabled: boolean;
}

export interface RuntimeUpdate {
  voice_enabled?: boolean;
  disabled_models?: string[];
  user_roles_enabled?: boolean;
  generation_paused?: boolean;
  max_tokens?: number;
  vision_enabled?: boolean;
  vision_model?: string;
  vision_provider?: string;
  vision_premium_only?: boolean;
  welcome_message?: string;
  brand_name?: string;
  brand_tagline?: string;
  streaming_enabled?: boolean;
  scheduling_enabled?: boolean;
}

export interface BotTemplate {
  key: string;
  name: string;
  emoji: string;
  description: string;
}

export interface TemplatesResponse {
  templates: BotTemplate[];
}

export interface ConfigApplyResult {
  applied: string[];
  todo: string[];
}

export interface OnboardingState {
  onboarded: boolean;
  has_openrouter_key: boolean;
  system_prompt_is_default: boolean;
  tiers_count: number;
  providers_configured: number;
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

export interface ProviderTestResult {
  ok: boolean;
  detail: string;
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
  price_stars: number; // 0 = free
  period_days: number; // billing period for paid tiers
  models: ModelSpec[];
}

export interface TiersResponse {
  tiers: TierConfig[];
}

export interface TierUpdate {
  key: string;
  name: string;
  daily_limit: number;
  price_stars: number;
  period_days: number;
  models: Array<{ provider: Provider; id: string }>;
}

export interface DayCount {
  day: string;
  count: number;
}

export interface ModelCount {
  model: string;
  count: number;
}

export interface AnalyticsResponse {
  messages: DayCount[];
  new_users: DayCount[];
  model_mix: ModelCount[];
  revenue_stars: number;
}

export interface BroadcastResponse {
  queued: number;
}
