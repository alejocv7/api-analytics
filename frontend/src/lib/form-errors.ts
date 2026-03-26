import type { FieldValues, Path, UseFormReturn } from "react-hook-form";
import type { ApiClientError } from "@/lib/api-client";

type ValidationDetail = {
  field: string | string[];
  message: string;
};

/**
 * Maps a 422 API validation error's `details` array to inline field errors on
 * the given form. Returns true if at least one field error was applied (so the
 * caller can skip showing a generic toast), false otherwise.
 */
export function applyApiFieldErrors<T extends FieldValues>(
  form: UseFormReturn<T>,
  err: ApiClientError,
): boolean {
  if (err.status !== 422 || !Array.isArray(err.details)) return false;

  let applied = false;
  for (const detail of err.details as ValidationDetail[]) {
    const segments = Array.isArray(detail.field)
      ? detail.field
      : [detail.field];
    // Pydantic prefixes paths with "body" — strip it
    const fieldPath = segments
      .filter((seg) => seg !== "body")
      .join(".");
    if (fieldPath) {
      const message = detail.message.replace(/^Value error,\s*/i, "");
      form.setError(fieldPath as Path<T>, { message });
      applied = true;
    }
  }
  return applied;
}