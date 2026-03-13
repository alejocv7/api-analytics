import { cn } from "@/lib/utils";

interface PageHeaderProps {
  title: React.ReactNode;
  description?: string;
  badges?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
  /** Breakpoint at which layout switches from column to row. Defaults to "md" */
  actionBreakpoint?: "sm" | "md" | "lg";
}

export function PageHeader({
  title,
  description,
  badges,
  action,
  className,
  actionBreakpoint = "md",
}: PageHeaderProps) {
  const layout = `${actionBreakpoint}:flex-row ${actionBreakpoint}:items-center ${actionBreakpoint}:justify-between`;
  const actionWidth = `w-full ${actionBreakpoint}:w-auto`;

  return (
    <div className={cn("flex flex-col gap-3", layout, className)}>
      <div className="space-y-1 min-w-0">
        <div className="flex items-center gap-2">
          <h1 className="text-xl font-semibold tracking-tight text-foreground whitespace-normal wrap-break-word capitalize">
            {title}
          </h1>
          {badges}
        </div>
        {description && (
          <p className="text-sm text-muted-foreground">{description}</p>
        )}
      </div>
      {action && <div className={cn("shrink-0", actionWidth)}>{action}</div>}
    </div>
  );
}
