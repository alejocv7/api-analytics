"use client";

import { useTransition } from "react";
import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { PaginationControls } from "@/components/shared/pagination-controls";
import { MethodBadge } from "@/components/shared/method-badge";
import { formatNumber, formatDuration, formatPercent, cn } from "@/lib/utils";
import type { EndpointStat, PaginatedResponse } from "@/types/api";

type SortField =
  | "request_count"
  | "avg_response_time_ms"
  | "error_rate"
  | "slowest_request_ms"
  | "fastest_request_ms";

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
  const ArrowIcon = currentOrder === "asc" ? ArrowUp : ArrowDown;

  return (
    <button
      onClick={() => onSort(field)}
      className={cn(
        "flex items-center gap-1 font-medium transition-colors group [text-transform:inherit]",
        isActive ? "text-primary" : "text-muted-foreground hover:text-primary",
      )}
    >
      <ArrowIcon
        className={cn(
          "h-3 w-3 shrink-0 transition-opacity",
          !isActive && "opacity-0 group-hover:opacity-40",
        )}
      />
      {children}
    </button>
  );
}

export function EndpointTable({
  data,
  isLoading,
  page: _page,
  onPageChange,
  sortBy,
  sortOrder,
  onSortChange,
}: EndpointTableProps) {
  const [, startTransition] = useTransition();

  function handleSort(field: SortField) {
    const newOrder = sortBy === field && sortOrder === "desc" ? "asc" : "desc";
    startTransition(() => {
      onSortChange(field, newOrder);
    });
  }

  if (isLoading) {
    return (
      <Card className="py-0 gap-0">
        <CardHeader className="px-5 pt-5 pb-5 gap-0">
          <Skeleton className="h-5 w-40" />
        </CardHeader>
        <CardContent className="px-5 pb-5 pt-0 space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </CardContent>
      </Card>
    );
  }

  const isEmpty = !data || data.items.length === 0;

  return (
    <Card className="py-0 gap-0">
      <CardHeader className="px-5 pt-5 pb-3 gap-0">
        <CardTitle className="tracking-tight text-base font-medium text-foreground/80">
          Endpoint Performance
        </CardTitle>
      </CardHeader>

      {isEmpty ? (
        <CardContent className="flex items-center justify-center h-32 text-sm text-muted-foreground">
          No endpoint data available
        </CardContent>
      ) : (
        <>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="border-t border-border bg-muted/50">
                  <TableHead className="pl-5 w-28 text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Method
                  </TableHead>
                  <TableHead className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    Path
                  </TableHead>
                  {/* Right-aligned headers to match right-aligned values */}
                  <TableHead className="w-32 text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    <div className="flex justify-end">
                      <SortButton
                        field="request_count"
                        currentField={sortBy}
                        currentOrder={sortOrder}
                        onSort={handleSort}
                      >
                        Requests
                      </SortButton>
                    </div>
                  </TableHead>
                  <TableHead className="w-28 text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    <div className="flex justify-end">
                      <SortButton
                        field="avg_response_time_ms"
                        currentField={sortBy}
                        currentOrder={sortOrder}
                        onSort={handleSort}
                      >
                        Avg
                      </SortButton>
                    </div>
                  </TableHead>
                  <TableHead className="w-28 text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    <div className="flex justify-end">
                      <SortButton
                        field="slowest_request_ms"
                        currentField={sortBy}
                        currentOrder={sortOrder}
                        onSort={handleSort}
                      >
                        Slowest
                      </SortButton>
                    </div>
                  </TableHead>
                  <TableHead className="w-28 text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    <div className="flex justify-end">
                      <SortButton
                        field="fastest_request_ms"
                        currentField={sortBy}
                        currentOrder={sortOrder}
                        onSort={handleSort}
                      >
                        Fastest
                      </SortButton>
                    </div>
                  </TableHead>
                  <TableHead className="w-24 pr-5 text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    <div className="flex justify-end">
                      <SortButton
                        field="error_rate"
                        currentField={sortBy}
                        currentOrder={sortOrder}
                        onSort={handleSort}
                      >
                        Error %
                      </SortButton>
                    </div>
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.items.map((endpoint, i) => (
                  <TableRow key={i}>
                    <TableCell className="pl-5">
                      <MethodBadge method={endpoint.method} />
                    </TableCell>
                    <TableCell>
                      <span className="text-sm font-mono text-foreground/70">
                        {endpoint.url_path}
                      </span>
                    </TableCell>
                    <TableCell className="text-sm text-right tabular-nums text-foreground/70">
                      {formatNumber(endpoint.request_count)}
                    </TableCell>
                    <TableCell className="text-sm text-right tabular-nums">
                      <span
                        className={cn(
                          endpoint.avg_response_time_ms > 1000
                            ? "text-destructive"
                            : endpoint.avg_response_time_ms > 500
                              ? "text-amber-500"
                              : "text-foreground/70",
                        )}
                      >
                        {formatDuration(endpoint.avg_response_time_ms)}
                      </span>
                    </TableCell>
                    <TableCell className="text-sm text-right tabular-nums text-foreground/70">
                      {formatDuration(endpoint.slowest_request_ms)}
                    </TableCell>
                    <TableCell className="text-sm text-right tabular-nums text-foreground/70">
                      {formatDuration(endpoint.fastest_request_ms)}
                    </TableCell>
                    <TableCell className="text-sm text-right tabular-nums pr-5">
                      <span
                        className={cn(
                          endpoint.error_rate > 1
                            ? "text-destructive"
                            : "text-foreground/70",
                        )}
                      >
                        {formatPercent(endpoint.error_rate)}
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {data.total > data.page_size && (
            <div className="px-5 py-3 border-t border-border">
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
    </Card>
  );
}
