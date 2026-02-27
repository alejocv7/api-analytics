// ============================================================
// Shared / Pagination
// ============================================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
  has_previous: boolean;
}

// ============================================================
// Error
// ============================================================

export interface ApiError {
  error: string;
  details?: Record<string, unknown> | unknown[] | null;
  request_id?: string | null;
}

// ============================================================
// Auth
// ============================================================

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginRequest {
  username: string; // backend uses OAuth2PasswordRequestForm with `username` field
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
}

// ============================================================
// User
// ============================================================

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

export interface UpdateUserRequest {
  full_name?: string;
}

// ============================================================
// Project
// ============================================================

export type ProjectRole = "owner" | "member" | "viewer";

export interface Project {
  id: string;
  name: string;
  project_key: string;
  description?: string | null;
  is_active: boolean;
  created_at: string;
  role?: ProjectRole; // injected client-side from membership info
}

export interface CreateProjectRequest {
  name: string;
  description?: string;
}

export interface UpdateProjectRequest {
  name?: string;
  description?: string;
  is_active?: boolean;
}

export interface ProjectWithStats extends Project {
  member_count?: number;
  api_key_count?: number;
}

// ============================================================
// API Key
// ============================================================

export type ApiKeyStatus = "active" | "inactive" | "expired";

export interface ApiKey {
  id: string;
  name: string;
  prefix: string;
  is_active: boolean;
  created_at: string;
  last_used_at?: string | null;
  expires_at?: string | null;
  total_requests: number;
}

export interface ApiKeyCreateResponse extends ApiKey {
  key: string; // plain-text key, shown only once
}

export interface CreateApiKeyRequest {
  name: string;
  expires_at?: string | null;
}

// ============================================================
// Member
// ============================================================

export interface Member {
  id: string;
  user_id: string;
  email: string;
  full_name: string;
  role: ProjectRole;
  joined_at: string;
}

export interface InviteMemberRequest {
  email: string;
  role: "member" | "viewer";
}

export interface UpdateMemberRoleRequest {
  role: "member" | "viewer";
}

// ============================================================
// Metrics
// ============================================================

export type Granularity = "minute" | "hour" | "day";

export interface MetricsSummary {
  request_count: number;
  avg_response_time_ms: number;
  requests_per_minute: number;
  error_count: number;
  error_rate: number;
  slowest_request_ms: number;
  fastest_request_ms: number;
}

export interface TimeSeriesPoint {
  timestamp: string;
  request_count: number;
  avg_response_time_ms: number;
  error_count: number;
}

export interface EndpointStat {
  url_path: string;
  method: string;
  request_count: number;
  avg_response_time_ms: number;
  error_count: number;
  error_rate: number;
  slowest_request_ms: number;
  fastest_request_ms: number;
}

export interface MetricsQueryParams {
  start_time: string;
  end_time: string;
  granularity?: Granularity;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}
