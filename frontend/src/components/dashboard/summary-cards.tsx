"use client";

import { Activity, AlertCircle, Clock, Zap } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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
}

function StatCard({ title, value, icon }: StatCardProps) {
  return (
    <Card className="gap-2 py-5">
      <CardHeader className="px-5 py-0 gap-0">
        <div className="flex items-center gap-2">
          <span className="text-muted-foreground/70">{icon}</span>
          <CardTitle className="text-sm font-medium text-muted-foreground">
            {title}
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent className="px-5">
        <p className="text-3xl font-bold text-foreground">{value}</p>
      </CardContent>
    </Card>
  );
}

function StatCardSkeleton() {
  return (
    <Card className="gap-2 py-5">
      <CardHeader className="px-5 py-0 gap-0">
        <div className="flex items-center gap-2">
          <Skeleton className="h-4 w-4" />
          <Skeleton className="h-4 w-28" />
        </div>
      </CardHeader>
      <CardContent className="px-5">
        <Skeleton className="h-9 w-24" />
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
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <StatCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        title="Total Requests"
        value={formatNumber(data.request_count)}
        icon={<Activity className="h-4 w-4" />}
      />
      <StatCard
        title="Avg Response Time"
        value={formatDuration(data.avg_response_time_ms)}
        icon={<Clock className="h-4 w-4" />}
      />
      <StatCard
        title="Error Rate"
        value={formatPercent(data.error_rate)}
        icon={<AlertCircle className="h-4 w-4" />}
      />
      <StatCard
        title="Requests/min"
        value={formatRpm(data.requests_per_minute)}
        icon={<Zap className="h-4 w-4" />}
      />
    </div>
  );
}
