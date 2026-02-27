import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface StatusBadgeProps {
  active: boolean;
  activeLabel?: string;
  inactiveLabel?: string;
  className?: string;
}

export function StatusBadge({
  active,
  activeLabel = "Active",
  inactiveLabel = "Inactive",
  className,
}: StatusBadgeProps) {
  return (
    <Badge
      variant={active ? "default" : "secondary"}
      className={cn(
        active
          ? "bg-green-100 text-green-700 hover:bg-green-100 border-green-200"
          : "bg-slate-100 text-slate-500 hover:bg-slate-100 border-slate-200",
        "text-xs font-medium",
        className,
      )}
    >
      <span
        className={cn(
          "mr-1.5 inline-block h-1.5 w-1.5 rounded-full",
          active ? "bg-green-500" : "bg-slate-400",
        )}
      />
      {active ? activeLabel : inactiveLabel}
    </Badge>
  );
}
