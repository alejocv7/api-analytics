"use client";

import Link from "next/link";
import { BarChart3, Key, Settings, Users } from "lucide-react";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/shared/status-badge";
import { RoleBadge } from "@/components/shared/role-badge";
import { formatDate } from "@/lib/utils";
import type { Project } from "@/types/api";

interface ProjectCardProps {
  project: Project;
}

export function ProjectCard({ project }: ProjectCardProps) {
  return (
    <Card className="flex flex-col hover:shadow-sm transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <CardTitle className="text-base font-semibold truncate">
              {project.name}
            </CardTitle>
            {project.description && (
              <p className="mt-1 text-sm text-muted-foreground line-clamp-2">
                {project.description}
              </p>
            )}
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {project.role && <RoleBadge role={project.role} />}
            <StatusBadge active={project.is_active} />
          </div>
        </div>
      </CardHeader>

      <CardContent className="pb-3 flex-1">
        <div className="flex items-center gap-1 text-xs text-muted-foreground font-mono bg-muted/50 rounded px-2 py-1.5">
          <Key className="h-3 w-3 shrink-0" />
          <span className="truncate">{project.project_key}</span>
        </div>
        <p className="mt-3 text-xs text-muted-foreground">
          Created {formatDate(project.created_at)}
        </p>
      </CardContent>

      <CardFooter className="pt-0 gap-2">
        <Button asChild size="sm" className="flex-1">
          <Link href={`/projects/${project.project_key}/analytics`}>
            <BarChart3 className="mr-1.5 h-3.5 w-3.5" />
            Analytics
          </Link>
        </Button>
        <Button asChild variant="outline" size="sm">
          <Link href={`/projects/${project.project_key}/settings`}>
            <Settings className="h-3.5 w-3.5" />
          </Link>
        </Button>
      </CardFooter>
    </Card>
  );
}
