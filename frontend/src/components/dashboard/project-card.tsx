"use client";

import Link from "next/link";
import { Copy, Key, Users } from "lucide-react";
import { toast } from "sonner";
import { Card, CardContent } from "@/components/ui/card";
import { StatusBadge } from "@/components/shared/status-badge";
import { formatDate } from "@/lib/utils";
import type { ProjectWithStats } from "@/types/api";
import { SecretDisplay } from "../shared/secret-display";

interface ProjectCardProps {
  project: ProjectWithStats;
}

export function ProjectCard({ project }: ProjectCardProps) {
  function copyKey() {
    navigator.clipboard.writeText(project.project_key);
    toast.success("Project key copied");
  }

  return (
    <Link href={`/projects/${project.project_key}/dashboard`}>
      <Card className="flex flex-col hover:shadow-md transition-shadow cursor-pointer">
        <CardContent className="px-5 space-y-2.5">
          {/* Header: name + status badge */}
          <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between sm:gap-2.5">
            <h3 className="text-base font-semibold leading-tight wrap-break-word">
              {project.name}
            </h3>
            <StatusBadge
              status={project.is_active ? "active" : "inactive"}
              className="px-1 py-0 h-4 self-start sm:shrink-0"
            />
          </div>

          <SecretDisplay
            value={project.project_key}
            label="Project Key"
            codeClassName="truncate"
          />

          {/* Footer: member count, key count, date */}
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <Users className="h-3.5 w-3.5" />
              {project.member_count}
            </span>
            <span className="flex items-center gap-1">
              <Key className="h-3.5 w-3.5" />
              {project.api_key_count}
            </span>
            <span className="ml-auto">
              Created {formatDate(project.created_at)}
            </span>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
