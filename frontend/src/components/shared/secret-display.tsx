import { CopyButton } from "@/components/shared/copy-button";
import { cn } from "@/lib/utils";

interface SecretDisplayProps {
  value: string;
  label?: string;
  className?: string;
  description?: string;
}

export function SecretDisplay({
  value,
  label,
  className,
  description,
}: SecretDisplayProps) {
  return (
    <div className={cn("space-y-1.5", className)}>
      {label && <p className="text-sm font-medium">{label}</p>}
      <div className="flex items-center gap-2 px-3 py-1 h-9 rounded-md bg-muted border border-border">
        <code className="flex-1 text-sm font-mono break-all text-muted-foreground">
          {value}
        </code>
        <CopyButton value={value} />
      </div>
      {description && (
        <p className="text-xs text-muted-foreground">{description}</p>
      )}
    </div>
  );
}
