"use client";

import { useState } from "react";
import { ArrowUpDown } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PaginationControls } from "@/components/shared/pagination-controls";
import {
  formatNumber,
  formatDuration,
  formatPercent,
  cn,
} from "@/lib/utils";
import type { EndpointStat, PaginatedResponse } from "@/types/api";

const METHOD_COLORS: Record<string, string> = {
  GET: "bg-blue-100 text-blue-700",
  POST: "bg-green-100 text-green-700",
  PUT: "bg-amber-100 text-amber-700",
  PATCH: "bg-orange-100 text-orange-700",
  DELETE: "bg-red-100 text-red-700",
};

type SortField =
  | "request_count"
  | "avg_response_time_ms"
  | "error_rate"
  | "slowest_request_ms";

interface SortState {
  field: SortField;
  order: "asc" | "desc";
}

interface EndpointTableProps {
  data?: PaginatedResponse<EndpointStat>;
  isLoading: boolean;
  page: number;
  onPageChange: (page: number) => void;
  sortBy: SortField;
  sortOrder: "asc" | "desc";
  onSortChange: (field: SortField, order: "asc" | "desc") => void;
}

function SortButton({
  field,
  currentField,
  currentOrder,
  onSort,
  children,
}: {
  field: SortField;
  currentField: SortField;
  currentOrder: "asc" | "desc";
  onSort: (field: SortField) => void;
  children: React.ReactNode;
}) {
  const isActive = currentField === field;
  return (
    <button
      onClick={() => onSort(field)}
      className={cn(
        "flex items-center gap-1 text-xs font-medium transition-colors",
        isActive ? "text-primary" : "text-muted-foreground hover:text-foreground",
      )}
    >
      {children}
      <ArrowUpDown className="h-3 w-3" />
    </button>
  );
}

export function EndpointTable({
  data,
  isLoading,
  page,
  onPageChange,
  sortBy,
  sortOrder,
  onSortChange,
}: EndpointTableProps) {
  function handleSort(field: SortField) {
    const newOrder =
      sortBy === field && sortOrder === "desc" ? "asc" : "desc";
    onSortChange(field, newOrder);
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-40" />
        </CardHeader>
        <CardContent>
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full mb-2" />
          ))}
        </CardContent>
      </Card>
    );
  }

  const isEmpty = !data || data.items.length === 0;

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base font-semibold">
          Endpoint Performance
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        {isEmpty ? (
          <div className="flex items-center justify-center h-32 text-sm text-muted-foreground">
            No endpoint data available
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent">
                    <TableHead className="pl-6 text-xs">Endpoint</TableHead>
                    <TableHead className="w-20">
                      <SortButton
                        field="request_count"
                        currentField={sortBy}
                        currentOrder={sortOrder}
                        onSort={handleSort}
                      >
                        Requests
                      </SortButton>
                    </TableHead>
                    <TableHead className="w-32">
                      <SortButton
                        field="avg_response_time_ms"
                        currentField={sortBy}
                        currentOrder={sortOrder}
                        onSort={handleSort}
                      >
                        Avg Response
                      </SortButton>
                    </TableHead>
                    <TableHead className="w-24">
                      <SortButton
                        field="error_rate"
                        currentField={sortBy}
                        currentOrder={sortOrder}
                        onSort={handleSort}
                      >
                        Error Rate
                      </SortButton>
                    </TableHead>
                    <TableHead className="w-28">
                      <SortButton
                        field="slowest_request_ms"
                        currentField={sortBy}
                        currentOrder={sortOrder}
                        onSort={handleSort}
                      >
                        Slowest
                      </SortButton>
                    </TableHead>
                    <TableHead className="w-24 text-xs text-muted-foreground font-medium">
                      Fastest
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.items.map((endpoint, i) => (
                    <TableRow key={i}>
                      <TableCell className="pl-6">
                        <div className="flex items-center gap-2 min-w-0">
                          <Badge
                            variant="outline"
                            className={cn(
                              "text-xs font-mono font-medium shrink-0",
                              METHOD_COLORS[endpoint.method] ?? "bg-slate-100 text-slate-700",
                            )}
                          >
                            {endpoint.method}
                          </Badge>
                          <span className="text-sm font-mono truncate text-foreground">
                            {endpoint.url_path}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell className="text-sm font-medium">
                        {formatNumber(endpoint.request_count)}
                      </TableCell>
                      <TableCell className="text-sm">
                        <span
                          className={cn(
                            endpoint.avg_response_time_ms > 1000
                              ? "text-destructive"
                              : endpoint.avg_response_time_ms > 500
                                ? "text-amber-600"
                                : "text-foreground",
                          )}
                        >
                          {formatDuration(endpoint.avg_response_time_ms)}
                        </span>
                      </TableCell>
                      <TableCell className="text-sm">
                        <span
                          className={cn(
                            endpoint.error_rate > 5
                              ? "text-destructive font-medium"
                              : endpoint.error_rate > 1
                                ? "text-amber-600"
                                : "text-muted-foreground",
                          )}
                        >
                          {formatPercent(endpoint.error_rate)}
                        </span>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {formatDuration(endpoint.slowest_request_ms)}
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {formatDuration(endpoint.fastest_request_ms)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            {data.total > data.page_size && (
              <div className="px-6 py-3 border-t border-border">
                <PaginationControls
                  page={data.page}
                  total={data.total}
                  pageSize={data.page_size}
                  hasNext={data.has_next}
                  hasPrevious={data.has_previous}
                  onPageChange={onPageChange}
                />
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
