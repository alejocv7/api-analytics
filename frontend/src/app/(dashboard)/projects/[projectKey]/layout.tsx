"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { use } from "react";
import { BarChart3, Settings } from "lucide-react";
import { cn } from "@/lib/utils";
import { useProject } from "@/hooks/use-projects";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/shared/status-badge";
import { RoleBadge } from "@/components/shared/role-badge";

const tabs = [
  {
    href: (key: string) => `/projects/${key}/analytics`,
    label: "Analytics",
    icon: BarChart3,
    match: (path: string) => path.includes("/analytics"),
  },
  {
    href: (key: string) => `/projects/${key}/settings`,
    label: "Settings",
    icon: Settings,
    match: (path: string) => path.includes("/settings"),
  },
] as const;

export default function ProjectLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ projectKey: string }>;
}) {
  const { projectKey } = use(params);
  const pathname = usePathname();
  const { data: project, isLoading } = useProject(projectKey);

  return (
    <div className="space-y-0">
      {/* Project header */}
      <div className="pb-4 border-b border-border mb-0">
        <div className="flex items-center justify-between gap-4">
          <div className="min-w-0 space-y-1">
            {isLoading ? (
              <>
                <Skeleton className="h-6 w-48" />
                <Skeleton className="h-4 w-32" />
              </>
            ) : (
              <>
                <div className="flex items-center gap-2">
                  <h1 className="text-xl font-semibold truncate">
                    {project?.name}
                  </h1>
                  {project && <StatusBadge active={project.is_active} />}
                  {project?.role && <RoleBadge role={project.role} />}
                </div>
                {project?.description && (
                  <p className="text-sm text-muted-foreground truncate">
                    {project.description}
                  </p>
                )}
              </>
            )}
          </div>
        </div>

        {/* Tab navigation */}
        <nav className="flex gap-1 mt-4 -mb-px">
          {tabs.map((tab) => {
            const isActive = tab.match(pathname);
            return (
              <Link
                key={tab.label}
                href={tab.href(projectKey)}
                className={cn(
                  "flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-t-md border-b-2 transition-colors",
                  isActive
                    ? "border-primary text-primary"
                    : "border-transparent text-muted-foreground hover:text-foreground hover:border-border",
                )}
              >
                <tab.icon className="h-4 w-4" />
                {tab.label}
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="pt-6">{children}</div>
    </div>
  );
}
