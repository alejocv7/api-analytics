import type { MetricsQueryParams } from "@/types/api";

export const queryKeys = {
  // Auth
  me: () => ["me"] as const,

  // Projects
  projects: {
    all: () => ["projects"] as const,
    list: (params?: Record<string, unknown>) =>
      ["projects", "list", params] as const,
    detail: (projectKey: string) => ["projects", projectKey] as const,
    members: (projectKey: string) =>
      ["projects", projectKey, "members"] as const,
    apiKeys: (projectKey: string) =>
      ["projects", projectKey, "api-keys"] as const,
  },

  // Metrics
  metrics: {
    summary: (projectKey: string, params: Partial<MetricsQueryParams>) =>
      ["projects", projectKey, "metrics", "summary", params] as const,
    timeSeries: (projectKey: string, params: Partial<MetricsQueryParams>) =>
      ["projects", projectKey, "metrics", "time-series", params] as const,
    endpoints: (projectKey: string, params: Partial<MetricsQueryParams>) =>
      ["projects", projectKey, "metrics", "endpoints", params] as const,
  },
};
