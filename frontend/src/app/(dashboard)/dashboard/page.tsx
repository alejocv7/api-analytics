import type { Metadata } from "next";
import { PageHeader } from "@/components/layouts/page-header";
import { ProjectList } from "@/components/dashboard/project-list";
import { CreateProjectDialog } from "@/components/dashboard/create-project-dialog";

export const metadata: Metadata = {
  title: "Projects",
};

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        title="Projects"
        description="Manage and monitor all your projects"
        action={<CreateProjectDialog />}
      />
      <ProjectList />
    </div>
  );
}
