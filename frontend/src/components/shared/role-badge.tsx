import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import type { ProjectRole } from "@/types/api";

const roleConfig: Record<ProjectRole, { label: string; className: string }> = {
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

type EditableRole = Exclude<ProjectRole, "owner">;

interface RoleBadgeProps {
  role: ProjectRole;
  onChange?: (role: EditableRole) => void;
  className?: string;
}

export function RoleBadge({ role, onChange, className }: RoleBadgeProps) {
  const config = roleConfig[role];
  const baseClassName = cn("text-xs font-medium", config.className, className);

  if (onChange) {
    return (
      <Select value={role} onValueChange={(v) => onChange(v as EditableRole)}>
        <SelectTrigger
          className={cn(
            "h-auto! w-fit px-2 py-0.5 border rounded-full gap-1 shrink-0",
            baseClassName,
          )}
        >
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="member">{roleConfig.member.label}</SelectItem>
          <SelectItem value="viewer">{roleConfig.viewer.label}</SelectItem>
        </SelectContent>
      </Select>
    );
  }

  return (
    <Badge variant="outline" className={baseClassName}>
      {config.label}
    </Badge>
  );
}
