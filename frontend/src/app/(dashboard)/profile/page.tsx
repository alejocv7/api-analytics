"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import type { Metadata } from "next";

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
import { Separator } from "@/components/ui/separator";
import { PageHeader } from "@/components/layouts/page-header";
import { apiClient, ApiClientError } from "@/lib/api-client";
import { updateProfileSchema, type UpdateProfileFormValues } from "@/lib/validators";
import { formatDateTime } from "@/lib/utils";
import { useAuth } from "@/providers/auth-provider";
import type { User } from "@/types/api";

export default function ProfilePage() {
  const { user, refetchUser } = useAuth();

  const form = useForm<UpdateProfileFormValues>({
    resolver: zodResolver(updateProfileSchema),
    defaultValues: { full_name: user?.full_name ?? "" },
  });

  useEffect(() => {
    if (user) {
      form.reset({ full_name: user.full_name });
    }
  }, [user, form]);

  async function onSubmit(values: UpdateProfileFormValues) {
    try {
      await apiClient.patch<User>("/users/me", { full_name: values.full_name });
      await refetchUser();
      toast.success("Profile updated");
    } catch (err) {
      if (err instanceof ApiClientError) {
        toast.error(err.message || "Failed to update profile");
      } else {
        toast.error("An unexpected error occurred");
      }
    }
  }

  return (
    <div className="space-y-6 max-w-lg">
      <PageHeader title="Profile" description="Manage your account information" />

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Personal information</CardTitle>
          <CardDescription>Update your display name.</CardDescription>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-muted-foreground">
                  Email
                </label>
                <div className="px-3 py-2 rounded-md bg-muted text-sm text-muted-foreground">
                  {user?.email}
                </div>
              </div>

              <FormField
                control={form.control}
                name="full_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Full name</FormLabel>
                    <FormControl>
                      <Input placeholder="Jane Smith" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="space-y-1.5">
                <label className="text-sm font-medium text-muted-foreground">
                  Member since
                </label>
                <div className="px-3 py-2 rounded-md bg-muted text-sm text-muted-foreground">
                  {user?.created_at ? formatDateTime(user.created_at) : "—"}
                </div>
              </div>

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
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  );
}
