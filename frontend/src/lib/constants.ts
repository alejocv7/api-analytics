export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export const SESSION_COOKIE = "session";

export const DEFAULT_PAGE_SIZE = 20;

export const DATE_PRESETS = [
  { label: "Last 24 hours", hours: 24 },
  { label: "Last 7 days", hours: 24 * 7 },
  { label: "Last 30 days", hours: 24 * 30 },
] as const;

export const DEFAULT_GRANULARITY = "hour" as const;

export const MAX_DATE_RANGE_DAYS = 60;
export const MIN_DATE_RANGE_MINUTES = 1;

export const API_KEY_DEFAULT_EXPIRY_DAYS = 90;
