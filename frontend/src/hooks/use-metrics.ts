import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { queryKeys } from "@/lib/query-keys";
import type {
  MetricsSummary,
  TimeSeriesPoint,
  EndpointStat,
  PaginatedResponse,
  Granularity,
} from "@/types/api";
import { toISOString } from "@/lib/utils";

interface UseMetricsOptions {
  projectKey: string;
  startTime: Date;
  endTime: Date;
  granularity?: Granularity;
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
}

// Backend query param names: start_date / end_date (not start_time / end_time)
type BackendParams = Record<string, string | number | boolean | undefined | null>;

function buildParams(opts: UseMetricsOptions): BackendParams {
  return {
    start_date: toISOString(opts.startTime),
    end_date: toISOString(opts.endTime),
    granularity: opts.granularity,
    page: opts.page,
    page_size: opts.pageSize,
    sort_by: opts.sortBy,
    sort_order: opts.sortOrder,
  };
}

export function useMetricsSummary(opts: UseMetricsOptions) {
  const params = buildParams(opts);
  return useQuery({
    queryKey: queryKeys.metrics.summary(opts.projectKey, params),
    queryFn: () =>
      apiClient.get<MetricsSummary>(
        `/projects/${opts.projectKey}/metrics/summary`,
        params,
      ),
    enabled: Boolean(opts.projectKey),
  });
}

// Backend returns PaginatedResponse<TimeSeriesPoint>, not a plain array.
// The hook exposes .data.items so callers get the array directly.
export function useTimeSeries(opts: UseMetricsOptions) {
  const params = buildParams(opts);
  return useQuery({
    queryKey: queryKeys.metrics.timeSeries(opts.projectKey, params),
    queryFn: async () => {
      const res = await apiClient.get<PaginatedResponse<TimeSeriesPoint>>(
        `/projects/${opts.projectKey}/metrics/time-series`,
        params,
      );
      return res.items;
    },
    enabled: Boolean(opts.projectKey),
  });
}

export function useEndpointStats(opts: UseMetricsOptions) {
  const params = buildParams(opts);
  return useQuery({
    queryKey: queryKeys.metrics.endpoints(opts.projectKey, params),
    queryFn: () =>
      apiClient.get<PaginatedResponse<EndpointStat>>(
        `/projects/${opts.projectKey}/metrics/endpoints`,
        params,
      ),
    enabled: Boolean(opts.projectKey),
  });
}
