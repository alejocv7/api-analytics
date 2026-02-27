import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { queryKeys } from "@/lib/query-keys";
import type {
  MetricsSummary,
  TimeSeriesPoint,
  EndpointStat,
  PaginatedResponse,
  MetricsQueryParams,
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

function buildParams(opts: UseMetricsOptions): Partial<MetricsQueryParams> {
  return {
    start_time: toISOString(opts.startTime),
    end_time: toISOString(opts.endTime),
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
        params as Record<string, string | number | boolean | undefined | null>,
      ),
    enabled: Boolean(opts.projectKey),
  });
}

export function useTimeSeries(opts: UseMetricsOptions) {
  const params = buildParams(opts);
  return useQuery({
    queryKey: queryKeys.metrics.timeSeries(opts.projectKey, params),
    queryFn: () =>
      apiClient.get<TimeSeriesPoint[]>(
        `/projects/${opts.projectKey}/metrics/time-series`,
        params as Record<string, string | number | boolean | undefined | null>,
      ),
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
        params as Record<string, string | number | boolean | undefined | null>,
      ),
    enabled: Boolean(opts.projectKey),
  });
}
