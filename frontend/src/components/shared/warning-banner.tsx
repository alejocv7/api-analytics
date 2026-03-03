import { AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface WarningBannerProps {
  children: React.ReactNode;
  className?: string;
}

export function WarningBanner({ children, className }: WarningBannerProps) {
  return (
    <div
      className={cn(
        "flex gap-3 p-3 rounded-lg bg-amber-50 border border-amber-200 dark:bg-amber-950/20 dark:border-amber-900/50",
        className,
      )}
    >
      <AlertCircle className="h-4 w-4 text-amber-600 dark:text-amber-500 mt-0.5 shrink-0" />
      <div className="text-sm text-amber-800 dark:text-amber-200">
        {children}
      </div>
    </div>
  );
}
