import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { ProjectRole } from "@/types/api";

const roleConfig: Record<
  ProjectRole,
  { label: string; className: string }
> = {
  owner: {
    label: "Owner",
    className:
      "bg-indigo-100 text-indigo-700 border-indigo-200 hover:bg-indigo-100 dark:bg-indigo-950/60 dark:text-indigo-400 dark:border-indigo-800 dark:hover:bg-indigo-950/60",
  },
  member: {
    label: "Member",
    className:
      "bg-blue-100 text-blue-700 border-blue-200 hover:bg-blue-100 dark:bg-blue-950/60 dark:text-blue-400 dark:border-blue-800 dark:hover:bg-blue-950/60",
  },
  viewer: {
    label: "Viewer",
    className:
      "bg-slate-100 text-slate-600 border-slate-200 hover:bg-slate-100 dark:bg-slate-800/60 dark:text-slate-400 dark:border-slate-700 dark:hover:bg-slate-800/60",
  },
};

interface RoleBadgeProps {
  role: ProjectRole;
  className?: string;
}

export function RoleBadge({ role, className }: RoleBadgeProps) {
  const config = roleConfig[role];
  return (
    <Badge
      variant="outline"
      className={cn("text-xs font-medium", config.className, className)}
    >
      {config.label}
    </Badge>
  );
}
