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
import { Button } from "@/components/ui/button";
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
    stroke: "var(--chart-1)",
    fill: "var(--chart-1)",
  },
  errors: {
    stroke: "var(--chart-3)",
    fill: "var(--chart-3)",
  },
  response_time: {
    stroke: "var(--chart-2)",
    fill: "var(--chart-2)",
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
          <div className="flex items-center rounded-lg border border-border p-1 bg-muted/30">
            <Button
              variant={mode === "requests" ? "default" : "ghost"}
              size="sm"
              onClick={() => setMode("requests")}
              className="h-7 px-3 text-xs shadow-none"
            >
              Requests
            </Button>
            <Button
              variant={mode === "response_time" ? "default" : "ghost"}
              size="sm"
              onClick={() => setMode("response_time")}
              className="h-7 px-3 text-xs shadow-none"
            >
              Response Time
            </Button>
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
                stroke="var(--border)"
                horizontal
                vertical={false}
              />

              <XAxis
                dataKey="timestamp"
                tickFormatter={formatXAxis}
                tick={{
                  fontSize: 11,
                  fill: "var(--muted-foreground)",
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
                  fill: "var(--muted-foreground)",
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
