"use client";

import { Activity, AlertCircle, Clock, TrendingDown, TrendingUp, Zap } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  formatNumber,
  formatDuration,
  formatPercent,
  formatRpm,
} from "@/lib/utils";
import type { MetricsSummary } from "@/types/api";

interface StatCardProps {
  title: string;
  value: string;
  icon: React.ReactNode;
  description?: string;
  highlight?: "success" | "warning" | "error";
}

function StatCard({ title, value, icon, description, highlight }: StatCardProps) {
  return (
    <Card>
      <CardHeader className="pb-2 flex flex-row items-center justify-between space-y-0">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        <span className="text-muted-foreground">{icon}</span>
      </CardHeader>
      <CardContent>
        <div
          className={
            highlight === "error"
              ? "text-destructive"
              : highlight === "warning"
                ? "text-amber-600"
                : highlight === "success"
                  ? "text-green-600"
                  : "text-foreground"
          }
        >
          <span className="text-2xl font-bold">{value}</span>
        </div>
        {description && (
          <p className="text-xs text-muted-foreground mt-1">{description}</p>
        )}
      </CardContent>
    </Card>
  );
}

function StatCardSkeleton() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <Skeleton className="h-4 w-28" />
      </CardHeader>
      <CardContent>
        <Skeleton className="h-8 w-20 mb-1" />
        <Skeleton className="h-3 w-32" />
      </CardContent>
    </Card>
  );
}

interface SummaryCardsProps {
  data?: MetricsSummary;
  isLoading: boolean;
}

export function SummaryCards({ data, isLoading }: SummaryCardsProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <StatCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (!data) return null;

  const errorRate = data.error_rate;

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
      <StatCard
        title="Total Requests"
        value={formatNumber(data.request_count)}
        icon={<Activity className="h-4 w-4" />}
      />
      <StatCard
        title="Req / Minute"
        value={formatRpm(data.requests_per_minute)}
        icon={<Zap className="h-4 w-4" />}
      />
      <StatCard
        title="Avg Response"
        value={formatDuration(data.avg_response_time_ms)}
        icon={<Clock className="h-4 w-4" />}
        highlight={
          data.avg_response_time_ms > 1000
            ? "error"
            : data.avg_response_time_ms > 500
              ? "warning"
              : undefined
        }
      />
      <StatCard
        title="Error Rate"
        value={formatPercent(errorRate)}
        icon={<AlertCircle className="h-4 w-4" />}
        highlight={
          errorRate > 5
            ? "error"
            : errorRate > 1
              ? "warning"
              : errorRate === 0
                ? "success"
                : undefined
        }
        description={`${formatNumber(data.error_count)} errors`}
      />
      <StatCard
        title="Slowest"
        value={formatDuration(data.slowest_request_ms)}
        icon={<TrendingDown className="h-4 w-4" />}
        highlight={data.slowest_request_ms > 2000 ? "warning" : undefined}
      />
      <StatCard
        title="Fastest"
        value={formatDuration(data.fastest_request_ms)}
        icon={<TrendingUp className="h-4 w-4" />}
        highlight="success"
      />
    </div>
  );
}
