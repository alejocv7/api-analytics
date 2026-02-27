"use client";

import { useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { format } from "date-fns";
import { formatDuration, formatNumber } from "@/lib/utils";
import type { TimeSeriesPoint } from "@/types/api";

type MetricMode = "requests" | "response_time";

interface TimeSeriesChartProps {
  data?: TimeSeriesPoint[];
  isLoading: boolean;
}

function formatXAxis(timestamp: string): string {
  return format(new Date(timestamp), "MMM d HH:mm");
}

const COLORS = {
  requests: "#4f46e5",   // indigo-600
  response_time: "#0d9488", // teal-600
  errors: "#ef4444",     // red-500
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
    <div className="rounded-lg border border-border bg-popover p-3 shadow-md text-sm">
      <p className="font-medium text-foreground mb-2">
        {format(new Date(label), "MMM d, yyyy HH:mm")}
      </p>
      {payload.map((entry) => (
        <div key={entry.name} className="flex items-center gap-2">
          <span
            className="inline-block w-2.5 h-2.5 rounded-full"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-muted-foreground">{entry.name}:</span>
          <span className="font-medium text-foreground">
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

  // Recharts requires a plain array; guard against unexpected API response shapes
  const chartData = Array.isArray(data) ? data : [];

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-64 w-full" />
        </CardContent>
      </Card>
    );
  }

  const isEmpty = chartData.length === 0;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-4">
        <CardTitle className="text-base font-semibold">
          {mode === "requests" ? "Request Volume" : "Response Time"}
        </CardTitle>
        <Tabs
          value={mode}
          onValueChange={(v) => setMode(v as MetricMode)}
        >
          <TabsList className="h-8">
            <TabsTrigger value="requests" className="text-xs px-3">
              Requests
            </TabsTrigger>
            <TabsTrigger value="response_time" className="text-xs px-3">
              Response Time
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </CardHeader>

      <CardContent>
        {isEmpty ? (
          <div className="flex items-center justify-center h-64 text-sm text-muted-foreground">
            No data for this time range
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={256}>
            <LineChart
              data={chartData}
              margin={{ top: 4, right: 16, left: 0, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis
                dataKey="timestamp"
                tickFormatter={formatXAxis}
                tick={{ fontSize: 11, fill: "#64748b" }}
                tickLine={false}
                axisLine={{ stroke: "#e2e8f0" }}
                minTickGap={60}
              />
              <YAxis
                tickFormatter={(v) =>
                  mode === "requests"
                    ? formatNumber(v)
                    : `${Math.round(v)}ms`
                }
                tick={{ fontSize: 11, fill: "#64748b" }}
                tickLine={false}
                axisLine={false}
                width={52}
              />
              <Tooltip
                content={<CustomTooltip mode={mode} />}
              />
              {mode === "requests" ? (
                <>
                  <Line
                    type="monotone"
                    dataKey="request_count"
                    name="Requests"
                    stroke={COLORS.requests}
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="error_count"
                    name="Errors"
                    stroke={COLORS.errors}
                    strokeWidth={1.5}
                    dot={false}
                    activeDot={{ r: 3 }}
                    strokeDasharray="4 2"
                  />
                </>
              ) : (
                <Line
                  type="monotone"
                  dataKey="avg_response_time_ms"
                  name="Avg Response (ms)"
                  stroke={COLORS.response_time}
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4 }}
                />
              )}
              <Legend
                iconType="plainline"
                wrapperStyle={{ fontSize: 12, paddingTop: 12 }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
