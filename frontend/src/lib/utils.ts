import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { format, formatDistanceToNow } from "date-fns";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// ============================================================
// Number formatters
// ============================================================

export function formatNumber(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
  return value.toLocaleString();
}

export function formatPercent(value: number, decimals = 1): string {
  return `${value.toFixed(decimals)}%`;
}

export function formatDuration(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

export function formatRpm(value: number): string {
  return `${value.toFixed(1)}/min`;
}

// ============================================================
// Date formatters
// ============================================================

export function formatDate(
  date: string | Date | null | undefined,
  fmt = "MMM d, yyyy",
): string {
  if (!date) return "—";
  const d = new Date(date);
  if (isNaN(d.getTime())) return "—";
  return format(d, fmt);
}

export function formatDateTime(date: string | Date | null | undefined): string {
  if (!date) return "—";
  const d = new Date(date);
  if (isNaN(d.getTime())) return "—";
  return format(d, "MMM d, yyyy HH:mm");
}

export function formatRelative(date: string | Date | null | undefined): string {
  if (!date) return "—";
  const d = new Date(date);
  if (isNaN(d.getTime())) return "—";
  return formatDistanceToNow(d, { addSuffix: true });
}

export function toISOString(date: Date): string {
  return date.toISOString();
}

// ============================================================
// API key helpers
// ============================================================

export function maskApiKey(prefix: string): string {
  return `${prefix}${"•".repeat(24)}`;
}
