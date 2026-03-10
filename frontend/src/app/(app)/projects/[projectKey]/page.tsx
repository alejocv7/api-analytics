import { redirect } from "next/navigation";
import { use } from "react";

export default function ProjectIndexPage({
  params,
}: {
  params: Promise<{ projectKey: string }>;
}) {
  const { projectKey } = use(params);
  redirect(`/projects/${projectKey}/dashboard`);
}
