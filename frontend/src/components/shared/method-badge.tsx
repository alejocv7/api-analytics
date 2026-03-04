import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const methodBadgeVariants = cva(
  "inline-flex items-center px-1.5 py-0.5 rounded border text-2xs font-semibold uppercase tracking-wider transition-colors",
  {
    variants: {
      method: {
        GET: "bg-violet-100 text-violet-700 border-violet-200 dark:bg-violet-900/30 dark:text-violet-400 dark:border-violet-800",
        POST: "bg-green-100 text-green-700 border-green-200 dark:bg-green-900/30 dark:text-green-400 dark:border-green-800",
        PUT: "bg-slate-100 text-slate-600 border-slate-200 dark:bg-slate-800/50 dark:text-slate-400 dark:border-slate-700",
        PATCH:
          "bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-800",
        DELETE:
          "bg-red-100 text-red-700 border-red-200 dark:bg-red-900/30 dark:text-red-400 dark:border-red-800",
        UNKNOWN:
          "bg-slate-100 text-slate-500 border-slate-200 dark:bg-slate-800/50 dark:text-slate-400 dark:border-slate-700",
      },
    },
    defaultVariants: {
      method: "GET",
    },
  },
);

export interface MethodBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  method?: string;
}

const KNOWN_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"];

export function MethodBadge({
  method = "GET",
  className,
  ...props
}: MethodBadgeProps) {
  const upperMethod = (method || "GET").toUpperCase();
  const variant = KNOWN_METHODS.includes(upperMethod) ? upperMethod : "UNKNOWN";

  return (
    <span
      className={cn(methodBadgeVariants({ method: variant as any }), className)}
      {...props}
    >
      {upperMethod}
    </span>
  );
}
