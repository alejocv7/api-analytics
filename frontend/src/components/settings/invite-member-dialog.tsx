"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { Loader2, UserPlus } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useInviteMember } from "@/hooks/use-members";
import { inviteMemberSchema, type InviteMemberFormValues } from "@/lib/validators";
import { ApiClientError } from "@/lib/api-client";
import { applyApiFieldErrors } from "@/lib/form-errors";

interface InviteMemberDialogProps {
  projectKey: string;
}

export function InviteMemberDialog({ projectKey }: InviteMemberDialogProps) {
  const [open, setOpen] = useState(false);
  const inviteMember = useInviteMember(projectKey);

  const form = useForm<InviteMemberFormValues>({
    resolver: zodResolver(inviteMemberSchema),
    defaultValues: { email: "", role: "member" },
  });

  async function onSubmit(values: InviteMemberFormValues) {
    try {
      await inviteMember.mutateAsync({ email: values.email, role: values.role });
      toast.success(`Invited ${values.email} as ${values.role}`);
      setOpen(false);
      form.reset();
    } catch (err) {
      if (err instanceof ApiClientError) {
        if (err.status === 404) {
          form.setError("email", { message: err.message });
        } else if (err.status === 409) {
          form.setError("email", { message: err.message });
        } else if (!applyApiFieldErrors(form, err)) {
          toast.error(err.message || "Failed to invite member");
        }
      } else {
        toast.error("An unexpected error occurred");
      }
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="sm">
          <UserPlus className="mr-1.5 h-3.5 w-3.5" />
          Invite member
        </Button>
      </DialogTrigger>

      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Invite team member</DialogTitle>
          <DialogDescription>
            Add a collaborator to this project.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email address</FormLabel>
                  <FormControl>
                    <Input
                      type="email"
                      placeholder="colleague@example.com"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="role"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Role</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    defaultValue={field.value}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="member">
                        Member — can view analytics
                      </SelectItem>
                      <SelectItem value="viewer">
                        Viewer — read-only access
                      </SelectItem>
                    </SelectContent>
                  </Select>
                  <FormDescription>
                    Owner role cannot be assigned via invitation.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setOpen(false)}
                disabled={form.formState.isSubmitting}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={form.formState.isSubmitting}>
                {form.formState.isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Inviting…
                  </>
                ) : (
                  "Send invite"
                )}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
