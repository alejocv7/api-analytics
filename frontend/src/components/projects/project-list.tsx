"use client";

import { useState } from "react";
import { FolderKanban, Loader2 } from "lucide-react";
import { ProjectCard } from "./project-card";
import { CreateProjectDialog } from "./create-project-dialog";
import { EmptyState } from "@/components/shared/empty-state";
import { PaginationControls } from "@/components/shared/pagination-controls";
import { useProjects } from "@/hooks/use-projects";
import { Skeleton } from "@/components/ui/skeleton";

function ProjectCardSkeleton() {
  return (
    <div className="rounded-lg border border-border bg-card p-5 space-y-3">
      <div className="flex justify-between">
        <Skeleton className="h-5 w-36" />
        <Skeleton className="h-5 w-16" />
      </div>
      <Skeleton className="h-4 w-48" />
      <Skeleton className="h-8 w-full" />
      <div className="flex gap-2">
        <Skeleton className="h-8 flex-1" />
        <Skeleton className="h-8 w-10" />
      </div>
    </div>
  );
}

export function ProjectList() {
  const [page, setPage] = useState(1);
  const { data, isLoading, isError } = useProjects(page);

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <ProjectCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <EmptyState
        title="Failed to load projects"
        description="There was an error fetching your projects. Please try again."
      />
    );
  }

  if (!data || data.items.length === 0) {
    return (
      <EmptyState
        icon={FolderKanban}
        title="No projects yet"
        description="Create your first project to start monitoring your APIs."
        action={<CreateProjectDialog />}
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {data.items.map((project) => (
          <ProjectCard key={project.id} project={project} />
        ))}
      </div>

      {data.total > data.page_size && (
        <PaginationControls
          page={data.page}
          total={data.total}
          pageSize={data.page_size}
          hasNext={data.has_next}
          hasPrevious={data.has_previous}
          onPageChange={setPage}
        />
      )}
    </div>
  );
}
