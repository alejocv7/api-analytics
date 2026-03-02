"use client";

import Link from "next/link";
import { Copy, Key, Users } from "lucide-react";
import { toast } from "sonner";
import { Card, CardContent } from "@/components/ui/card";
import { formatDate } from "@/lib/utils";
import type { Project } from "@/types/api";

interface ProjectCardProps {
  project: Project;
}

export function ProjectCard({ project }: ProjectCardProps) {
  function copyKey() {
    navigator.clipboard.writeText(project.project_key);
    toast.success("Project key copied");
  }

  return (
    <Link href={`/projects/${project.project_key}/analytics`}>
      <Card className="flex flex-col hover:shadow-md transition-shadow cursor-pointer">
        <CardContent className="px-5 space-y-2.5">
          {/* Header: status dot + name */}
          <div className="flex items-center gap-2.5">
            <span
              className={`inline-block h-2.5 w-2.5 rounded-full shrink-0 ${project.is_active ? "bg-green-500" : "bg-slate-300"}`}
            />
            <h3 className="text-base font-semibold leading-tight break-words">
              {project.name}
            </h3>
          </div>

          {/* Project Key */}
          <div>
            <p className="text-xs text-muted-foreground mb-1.5">Project Key</p>
            <div
              className="flex items-center gap-2 bg-muted/60 rounded-md px-3 py-2 group"
              onClick={(e) => {
                e.preventDefault();
                copyKey();
              }}
            >
              <span className="flex-1 text-xs font-mono text-foreground truncate">
                {project.project_key}
              </span>
              <Copy className="h-3.5 w-3.5 text-muted-foreground group-hover:text-foreground transition-colors shrink-0" />
            </div>
          </div>

          {/* Footer: member count, key count, date */}
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <Users className="h-3.5 w-3.5" />
              {(project as Project & { member_count?: number }).member_count ??
                "—"}
            </span>
            <span className="flex items-center gap-1">
              <Key className="h-3.5 w-3.5" />
              {(project as Project & { api_key_count?: number })
                .api_key_count ?? "—"}
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
