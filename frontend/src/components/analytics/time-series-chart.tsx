"use client";

import { useState } from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
import {
  Card,
  CardAction,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { format } from "date-fns";
import { formatDuration, formatNumber } from "@/lib/utils";
import type { TimeSeriesPoint } from "@/types/api";

type MetricMode = "requests" | "response_time";

interface TimeSeriesChartProps {
  data?: TimeSeriesPoint[];
  isLoading: boolean;
}

// Use 24hr format
function formatXAxis(timestamp: string): string {
  return format(new Date(timestamp), "HH:mm");
}

const CHART_COLORS = {
  requests: {
    stroke: "#6366f1",
    fill: "#6366f1",
  },
  errors: {
    stroke: "#f87171",
    fill: "#f87171",
  },
  response_time: {
    stroke: "#0d9488",
    fill: "#0d9488",
  },
};

function CustomTooltip({
  active,
  payload,
  label,
  mode,
}: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string;
  mode: MetricMode;
}) {
  if (!active || !payload?.length || !label) return null;

  return (
    <div className="rounded-lg border border-border bg-popover p-3 shadow-lg text-sm">
      <p className="font-medium text-foreground mb-2">
        {format(new Date(label), "MMM d, yyyy HH:mm")}
      </p>
      {payload.map((entry) => (
        <div key={entry.name} className="flex items-center gap-2">
          <span
            className="inline-block w-2 h-2 rounded-full shrink-0"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-muted-foreground">{entry.name}:</span>
          <span className="font-semibold text-foreground">
            {mode === "requests"
              ? formatNumber(entry.value)
              : formatDuration(entry.value)}
          </span>
        </div>
      ))}
    </div>
  );
}

export function TimeSeriesChart({ data, isLoading }: TimeSeriesChartProps) {
  const [mode, setMode] = useState<MetricMode>("requests");

  const chartData = Array.isArray(data) ? data : [];

  if (isLoading) {
    return (
      <Card className="py-0 gap-0">
        <CardHeader className="px-5 pt-5 pb-5">
          <Skeleton className="h-5 w-36" />
          <CardAction>
            <Skeleton className="h-7 w-48" />
          </CardAction>
        </CardHeader>
        <CardContent className="px-5 pb-5 pt-0">
          <Skeleton className="h-64 w-full" />
        </CardContent>
      </Card>
    );
  }

  const isEmpty = chartData.length === 0;

  return (
    <Card className="py-0 gap-0">
      <CardHeader className="px-5 pt-5 pb-5">
        <CardTitle className="tracking-tight text-base font-medium text-foreground/80">
          {mode === "requests" ? "Request Volume" : "Response Time"}
        </CardTitle>

        <CardAction>
          {/* Connected pill toggle with border all the way around */}
          <div className="flex items-center rounded-md border border-border overflow-hidden">
            <button
              onClick={() => setMode("requests")}
              className={`px-4 py-1.5 text-sm font-medium transition-colors ${
                mode === "requests"
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
              }`}
            >
              Requests
            </button>
            <div className="w-px h-full bg-border self-stretch" />
            <button
              onClick={() => setMode("response_time")}
              className={`px-4 py-1.5 text-sm font-medium transition-colors ${
                mode === "response_time"
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
              }`}
            >
              Response Time
            </button>
          </div>
        </CardAction>
      </CardHeader>

      <CardContent className="px-5 pb-5 pt-0">
        {isEmpty ? (
          <div className="flex items-center justify-center h-64 text-sm text-muted-foreground">
            No data for this time range
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart
              data={chartData}
              margin={{ top: 4, right: 4, left: 0, bottom: 0 }}
            >
              <defs>
                {/* Gradient starts strong at top, fades to nothing at bottom */}
                <linearGradient id="gradRequests" x1="0" y1="0" x2="0" y2="1">
                  <stop
                    offset="0%"
                    stopColor={CHART_COLORS.requests.stroke}
                    stopOpacity={0.25}
                  />
                  <stop
                    offset="100%"
                    stopColor={CHART_COLORS.requests.stroke}
                    stopOpacity={0}
                  />
                </linearGradient>
                <linearGradient id="gradErrors" x1="0" y1="0" x2="0" y2="1">
                  <stop
                    offset="0%"
                    stopColor={CHART_COLORS.errors.stroke}
                    stopOpacity={0.15}
                  />
                  <stop
                    offset="100%"
                    stopColor={CHART_COLORS.errors.stroke}
                    stopOpacity={0}
                  />
                </linearGradient>
                <linearGradient id="gradResponse" x1="0" y1="0" x2="0" y2="1">
                  <stop
                    offset="0%"
                    stopColor={CHART_COLORS.response_time.stroke}
                    stopOpacity={0.2}
                  />
                  <stop
                    offset="100%"
                    stopColor={CHART_COLORS.response_time.stroke}
                    stopOpacity={0}
                  />
                </linearGradient>
              </defs>

              <CartesianGrid
                strokeDasharray="4 4"
                stroke="#e2e8f0"
                horizontal
                vertical
              />

              <XAxis
                dataKey="timestamp"
                tickFormatter={formatXAxis}
                tick={{
                  fontSize: 11,
                  fill: "#94a3b8",
                  fontFamily: "var(--font-mono)",
                }}
                tickLine={false}
                axisLine={false}
                minTickGap={80}
                dy={6}
                // Align ticks with grid lines
                interval="preserveStartEnd"
              />
              <YAxis
                tickFormatter={(v) =>
                  mode === "requests" ? formatNumber(v) : `${Math.round(v)}ms`
                }
                tick={{
                  fontSize: 11,
                  fill: "#94a3b8",
                  fontFamily: "var(--font-mono)",
                }}
                tickLine={false}
                axisLine={false}
                width={52}
              />

              <Tooltip content={<CustomTooltip mode={mode} />} />

              {mode === "requests" ? (
                <>
                  <Area
                    type="monotone"
                    dataKey="request_count"
                    name="Requests"
                    stroke={CHART_COLORS.requests.stroke}
                    strokeWidth={2}
                    fill="url(#gradRequests)"
                    dot={false}
                    activeDot={{ r: 4, strokeWidth: 0 }}
                  />
                  <Area
                    type="monotone"
                    dataKey="error_count"
                    name="Errors"
                    stroke={CHART_COLORS.errors.stroke}
                    strokeWidth={1.5}
                    fill="url(#gradErrors)"
                    dot={false}
                    activeDot={{ r: 3, strokeWidth: 0 }}
                    strokeDasharray="4 2"
                  />
                </>
              ) : (
                <Area
                  type="monotone"
                  dataKey="avg_response_time_ms"
                  name="Avg Response (ms)"
                  stroke={CHART_COLORS.response_time.stroke}
                  strokeWidth={2}
                  fill="url(#gradResponse)"
                  dot={false}
                  activeDot={{ r: 4, strokeWidth: 0 }}
                />
              )}
            </AreaChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
