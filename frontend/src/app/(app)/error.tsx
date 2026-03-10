"use client";

import { AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center h-64 text-center">
      <div className="flex items-center justify-center w-12 h-12 rounded-full bg-destructive/10 mb-4">
        <AlertCircle className="h-6 w-6 text-destructive" />
      </div>
      <h2 className="text-base font-semibold text-foreground">
        Something went wrong
      </h2>
      <p className="mt-1 text-sm text-muted-foreground max-w-sm">
        {error.message || "An unexpected error occurred. Please try again."}
      </p>
      <Button className="mt-4" variant="outline" size="sm" onClick={reset}>
        Try again
      </Button>
    </div>
  );
}
