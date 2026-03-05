"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { Loader2, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { SecretDisplay } from "@/components/shared/secret-display";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { useUpdateProject, useDeleteProject } from "@/hooks/use-projects";
import {
  updateProjectSchema,
  type UpdateProjectFormValues,
} from "@/lib/validators";
import { ApiClientError } from "@/lib/api-client";
import { applyApiFieldErrors } from "@/lib/form-errors";
import type { Project } from "@/types/api";

interface GeneralSettingsProps {
  project: Project;
  isOwner: boolean;
}

export function GeneralSettings({ project, isOwner }: GeneralSettingsProps) {
  const router = useRouter();
  const [deleteOpen, setDeleteOpen] = useState(false);

  const updateProject = useUpdateProject(project.project_key);
  const deleteProject = useDeleteProject(project.project_key);

  const form = useForm<UpdateProjectFormValues>({
    resolver: zodResolver(updateProjectSchema),
    defaultValues: {
      name: project.name,
      description: project.description ?? "",
      is_active: project.is_active,
    },
  });

  // Sync form if project data changes
  useEffect(() => {
    form.reset({
      name: project.name,
      description: project.description ?? "",
      is_active: project.is_active,
    });
  }, [project, form]);

  async function onSubmit(values: UpdateProjectFormValues) {
    try {
      await updateProject.mutateAsync({
        name: values.name,
        description: values.description || undefined,
        is_active: values.is_active,
      });
      toast.success("Project settings saved");
    } catch (err) {
      if (err instanceof ApiClientError) {
        if (err.status === 409) {
          form.setError("name", { message: err.message });
        } else if (!applyApiFieldErrors(form, err)) {
          toast.error("Failed to save settings");
        }
      } else {
        toast.error("Failed to save settings");
      }
    }
  }

  async function handleDelete() {
    try {
      await deleteProject.mutateAsync();
      toast.success("Project deleted");
      router.push("/dashboard");
    } catch {
      toast.error("Failed to delete project");
    }
  }

  return (
    <div className="space-y-6">
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          {/* Project details */}
          <Card>
            <CardHeader>
              <CardTitle>Project details</CardTitle>
              <CardDescription>
                Basic information about your project.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Name</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        disabled={!isOwner}
                        placeholder="Project name"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Description</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        disabled={!isOwner}
                        placeholder="Brief description of this project"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* Project key (read-only) */}
              <SecretDisplay
                value={project.project_key}
                label="Key"
                description="This key is auto-generated and used to identify your project."
              />

              <FormField
                control={form.control}
                name="is_active"
                render={({ field }) => (
                  <FormItem className="flex items-center justify-between pt-1">
                    <div>
                      <FormLabel>Active</FormLabel>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        Inactive projects stop accepting new metrics.
                      </p>
                    </div>
                    <FormControl>
                      <Switch
                        checked={field.value}
                        onCheckedChange={field.onChange}
                        disabled={!isOwner}
                      />
                    </FormControl>
                  </FormItem>
                )}
              />

              {isOwner && (
                <div className="flex justify-end">
                  <Button
                    type="submit"
                    disabled={
                      form.formState.isSubmitting || !form.formState.isDirty
                    }
                  >
                    {form.formState.isSubmitting ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Saving…
                      </>
                    ) : (
                      "Save changes"
                    )}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </form>
      </Form>

      {/* Danger zone */}
      {isOwner && (
        <Card className="border-destructive/30">
          <CardHeader>
            <CardTitle className="text-destructive">Danger zone</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">Delete this project</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Permanently removes all data, API keys, and metrics.
                </p>
              </div>
              <Button
                variant="destructive"
                size="sm"
                onClick={() => setDeleteOpen(true)}
              >
                <Trash2 className="mr-1.5 h-3.5 w-3.5" />
                Delete project
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <ConfirmDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        title="Delete project"
        description={`Permanently delete "${project.name}" and all its data? This action cannot be undone.`}
        confirmLabel="Delete project"
        isDestructive
        isLoading={deleteProject.isPending}
        onConfirm={handleDelete}
      />
    </div>
  );
}
