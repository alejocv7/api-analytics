import type { Metadata } from "next";
import { PageHeader } from "@/components/layouts/page-header";
import { ProjectList } from "@/components/projects/project-list";
import { CreateProjectDialog } from "@/components/projects/create-project-dialog";

export const metadata: Metadata = {
  title: "Projects",
};

export default function ProjectsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Projects"
        description="Manage and monitor all your projects"
        action={<CreateProjectDialog />}
        actionBreakpoint="sm"
      />
      <ProjectList />
    </div>
  );
}
