"use client";

import { use } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { GeneralSettings } from "@/components/settings/general-settings";
import { ApiKeysTab } from "@/components/settings/api-keys-tab";
import { MembersTab } from "@/components/settings/members-tab";
import { useProject } from "@/hooks/use-projects";
import { useCurrentMemberRole } from "@/hooks/use-members";
import { Skeleton } from "@/components/ui/skeleton";

export default function SettingsPage({
  params,
}: {
  params: Promise<{ projectKey: string }>;
}) {
  const { projectKey } = use(params);
  const { data: project, isLoading: projectLoading } = useProject(projectKey);
  const { role, isLoading: roleLoading } = useCurrentMemberRole(projectKey);

  const isLoading = projectLoading || roleLoading;
  const isOwner = role === "owner";

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="text-sm text-muted-foreground">Project not found.</div>
    );
  }

  return (
    <Tabs defaultValue="general">
      <TabsList className="mb-6">
        <TabsTrigger value="general">General</TabsTrigger>
        <TabsTrigger value="api-keys">API Keys</TabsTrigger>
        <TabsTrigger value="members">Members</TabsTrigger>
      </TabsList>

      <TabsContent value="general" className="mt-0">
        <GeneralSettings project={project} isOwner={isOwner} />
      </TabsContent>

      <TabsContent value="api-keys" className="mt-0">
        <ApiKeysTab projectKey={projectKey} isOwner={isOwner} />
      </TabsContent>

      <TabsContent value="members" className="mt-0">
        <MembersTab projectKey={projectKey} isOwner={isOwner} />
      </TabsContent>
    </Tabs>
  );
}
