"use client";

import { use, useState } from "react";
import { subHours } from "date-fns";
import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { SummaryCards } from "@/components/analytics/summary-cards";
import { TimeSeriesChart } from "@/components/analytics/time-series-chart";
import { EndpointTable } from "@/components/analytics/endpoint-table";
import { DateRangePicker, type DateRangeValue } from "@/components/analytics/date-range-picker";
import { GranularitySelect } from "@/components/analytics/granularity-select";
import {
  useMetricsSummary,
  useTimeSeries,
  useEndpointStats,
} from "@/hooks/use-metrics";
import { DEFAULT_GRANULARITY } from "@/lib/constants";
import type { Granularity } from "@/types/api";

type SortField = "request_count" | "avg_response_time_ms" | "error_rate" | "slowest_request_ms";

export default function AnalyticsPage({
  params,
}: {
  params: Promise<{ projectKey: string }>;
}) {
  const { projectKey } = use(params);

  const [dateRange, setDateRange] = useState<DateRangeValue>({
    startTime: subHours(new Date(), 24),
    endTime: new Date(),
  });
  const [granularity, setGranularity] = useState<Granularity>(DEFAULT_GRANULARITY);
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
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex flex-wrap items-center gap-3">
        <DateRangePicker value={dateRange} onChange={setDateRange} />
        <GranularitySelect value={granularity} onChange={setGranularity} />
        <Button
          variant="outline"
          size="sm"
          onClick={handleRefresh}
          className="h-9 gap-1.5"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh
        </Button>
      </div>

      {/* Summary cards */}
      <SummaryCards data={summary.data} isLoading={summary.isLoading} />

      {/* Time series chart */}
      <TimeSeriesChart
        data={timeSeries.data}
        isLoading={timeSeries.isLoading}
      />

      {/* Endpoint table */}
      <EndpointTable
        data={endpoints.data}
        isLoading={endpoints.isLoading}
        page={endpointPage}
        onPageChange={setEndpointPage}
        sortBy={sortBy}
        sortOrder={sortOrder}
        onSortChange={handleSortChange}
      />
    </div>
  );
}
