"use client";

import { use, useState } from "react";
import { subHours } from "date-fns";
import { RefreshCw, TrendingDown, TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { SummaryCards } from "@/components/analytics/summary-cards";
import { TimeSeriesChart } from "@/components/analytics/time-series-chart";
import {
  EndpointTable,
  type SortField,
} from "@/components/analytics/endpoint-table";
import {
  DateRangePicker,
  type DateRangeValue,
} from "@/components/analytics/date-range-picker";
import { GranularitySelect } from "@/components/analytics/granularity-select";
import { PageHeader } from "@/components/layouts/page-header";
import { StatusBadge } from "@/components/shared/status-badge";
import { RoleBadge } from "@/components/shared/role-badge";
import {
  useMetricsSummary,
  useTimeSeries,
  useEndpointStats,
} from "@/hooks/use-metrics";
import { useProject } from "@/hooks/use-projects";
import { DEFAULT_GRANULARITY } from "@/lib/constants";
import type { Granularity } from "@/types/api";

function EndpointHighlightRow({
  projectKey,
  startTime,
  endTime,
  granularity,
}: {
  projectKey: string;
  startTime: Date;
  endTime: Date;
  granularity: Granularity;
}) {
  const slowestQuery = useEndpointStats({
    projectKey,
    startTime,
    endTime,
    granularity,
    page: 1,
    pageSize: 1,
    sortBy: "avg_response_time_ms",
    sortOrder: "desc",
  });

  const fastestQuery = useEndpointStats({
    projectKey,
    startTime,
    endTime,
    granularity,
    page: 1,
    pageSize: 1,
    sortBy: "avg_response_time_ms",
    sortOrder: "asc",
  });

  const slowest = slowestQuery.data?.items[0];
  const fastest = fastestQuery.data?.items[0];

  if (slowestQuery.isLoading || fastestQuery.isLoading) {
    return (
      <div className="grid grid-cols-2 gap-4">
        <Skeleton className="h-16 rounded-xl" />
        <Skeleton className="h-16 rounded-xl" />
      </div>
    );
  }

  if (!slowest && !fastest) return null;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {slowest && (
        <div className="flex items-center gap-3 px-5 py-4 rounded-xl border border-border bg-card">
          <TrendingDown className="h-4 w-4 text-red-400 shrink-0" />
          <div className="min-w-0">
            <p className="text-xs text-muted-foreground mb-0.5">
              Slowest Endpoint
            </p>
            <p className="text-sm font-mono truncate text-foreground/80">
              {slowest.url_path}
            </p>
          </div>
        </div>
      )}
      {fastest && (
        <div className="flex items-center gap-3 px-5 py-4 rounded-xl border border-border bg-card">
          <TrendingUp className="h-4 w-4 text-indigo-400 shrink-0" />
          <div className="min-w-0">
            <p className="text-xs text-muted-foreground mb-0.5">
              Fastest Endpoint
            </p>
            <p className="text-sm font-mono truncate text-foreground/80">
              {fastest.url_path}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default function DashboardPage({
  params,
}: {
  params: Promise<{ projectKey: string }>;
}) {
  const { projectKey } = use(params);
  const { data: project } = useProject(projectKey);

  const [dateRange, setDateRange] = useState<DateRangeValue>({
    startTime: subHours(new Date(), 24),
    endTime: new Date(),
  });
  const [granularity, setGranularity] =
    useState<Granularity>(DEFAULT_GRANULARITY);
  const [endpointPage, setEndpointPage] = useState(1);
  const [sortBy, setSortBy] = useState<SortField>("request_count");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  const metricsOpts = {
    projectKey,
    startTime: dateRange.startTime,
    endTime: dateRange.endTime,
    granularity,
  };

  const summary = useMetricsSummary(metricsOpts);
  const timeSeries = useTimeSeries(metricsOpts);
  const endpoints = useEndpointStats({
    ...metricsOpts,
    page: endpointPage,
    pageSize: 20,
    sortBy,
    sortOrder,
  });

  function handleSortChange(field: SortField, order: "asc" | "desc") {
    setSortBy(field);
    setSortOrder(order);
    setEndpointPage(1);
  }

  function handleRefresh() {
    setDateRange((prev) => ({ ...prev, endTime: new Date() }));
  }

  return (
    <div className="space-y-5">
      <PageHeader
        title={project?.name ?? <Skeleton className="h-6 w-48" />}
        description="API performance overview"
        badges={
          project && (
            <>
              <StatusBadge status={project.is_active ? "active" : "inactive"} />
              {project.role && <RoleBadge role={project.role} />}
            </>
          )
        }
        action={
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <DateRangePicker value={dateRange} onChange={setDateRange} />
            <div className="flex items-center gap-2">
              <GranularitySelect
                value={granularity}
                onChange={setGranularity}
                className="flex-1 sm:flex-none"
              />
              <Button
                variant="outline"
                size="icon"
                onClick={handleRefresh}
                className="h-9 w-9 shrink-0"
                title="Refresh"
              >
                <RefreshCw className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>
        }
      />

      <SummaryCards data={summary.data} isLoading={summary.isLoading} />

      <TimeSeriesChart
        data={timeSeries.data}
        isLoading={timeSeries.isLoading}
      />

      <EndpointHighlightRow
        projectKey={projectKey}
        startTime={dateRange.startTime}
        endTime={dateRange.endTime}
        granularity={granularity}
      />

      <EndpointTable
        data={endpoints.data}
        isLoading={endpoints.isLoading}
        onPageChange={setEndpointPage}
        sortBy={sortBy}
        sortOrder={sortOrder}
        onSortChange={handleSortChange}
      />
    </div>
  );
}
