import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface StatusBadgeProps {
  status: "active" | "inactive" | "expired";
  className?: string;
  label?: string;
}

const STATUS_CONFIG = {
  active: {
    label: "Active",
    badgeClass:
      "bg-green-100 text-green-700 hover:bg-green-100 border-green-200 dark:bg-green-900/30 dark:text-green-400 dark:border-green-800",
    dotClass: "bg-green-500",
  },
  inactive: {
    label: "Inactive",
    badgeClass:
      "bg-slate-100 text-slate-500 hover:bg-slate-100 border-slate-200 dark:bg-slate-800/50 dark:text-slate-400 dark:border-slate-700",
    dotClass: "bg-slate-400",
  },
  expired: {
    label: "Expired",
    badgeClass:
      "bg-red-50 text-red-600 hover:bg-red-50 border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-900/50",
    dotClass: "bg-red-500",
  },
};

export function StatusBadge({ status, className, label }: StatusBadgeProps) {
  const config = STATUS_CONFIG[status];
  const displayLabel = label || config.label;

  return (
    <Badge
      variant="outline"
      className={cn(
        config.badgeClass,
        "text-xs font-medium px-2 py-0.5",
        className,
      )}
    >
      <span
        className={cn(
          "mr-1.5 inline-block h-1.5 w-1.5 rounded-full",
          config.dotClass,
        )}
      />
      {displayLabel}
    </Badge>
  );
}
