"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { AlertCircle, Key, Loader2, Plus } from "lucide-react";
import { addDays, format } from "date-fns";

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
import { CopyButton } from "@/components/shared/copy-button";
import { useCreateApiKey } from "@/hooks/use-api-keys";
import {
  createApiKeySchema,
  type CreateApiKeyFormValues,
} from "@/lib/validators";
import { ApiClientError } from "@/lib/api-client";
import { API_KEY_DEFAULT_EXPIRY_DAYS } from "@/lib/constants";
import type { ApiKeyCreateResponse } from "@/types/api";

interface CreateApiKeyDialogProps {
  projectKey: string;
}

export function CreateApiKeyDialog({ projectKey }: CreateApiKeyDialogProps) {
  const [open, setOpen] = useState(false);
  const [createdKey, setCreatedKey] = useState<ApiKeyCreateResponse | null>(null);
  const [acknowledged, setAcknowledged] = useState(false);

  const createApiKey = useCreateApiKey(projectKey);

  const form = useForm<CreateApiKeyFormValues>({
    resolver: zodResolver(createApiKeySchema),
    defaultValues: {
      name: "",
      expires_at: format(addDays(new Date(), API_KEY_DEFAULT_EXPIRY_DAYS), "yyyy-MM-dd"),
    },
  });

  function handleOpenChange(nextOpen: boolean) {
    // Prevent closing if key was created but not acknowledged
    if (!nextOpen && createdKey && !acknowledged) return;
    if (!nextOpen) {
      form.reset();
      setCreatedKey(null);
      setAcknowledged(false);
    }
    setOpen(nextOpen);
  }

  async function onSubmit(values: CreateApiKeyFormValues) {
    try {
      const key = await createApiKey.mutateAsync({
        name: values.name,
        expires_at: values.expires_at ?? null,
      });
      setCreatedKey(key);
    } catch (err) {
      if (err instanceof ApiClientError) {
        toast.error(err.message || "Failed to create API key");
      } else {
        toast.error("An unexpected error occurred");
      }
    }
  }

  function handleDone() {
    setAcknowledged(true);
    setOpen(false);
    form.reset();
    setCreatedKey(null);
    setAcknowledged(false);
    toast.success("API key saved successfully");
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button size="sm">
          <Plus className="mr-1.5 h-3.5 w-3.5" />
          Generate key
        </Button>
      </DialogTrigger>

      <DialogContent
        className="sm:max-w-md"
        onInteractOutside={(e) => {
          if (createdKey && !acknowledged) e.preventDefault();
        }}
        onEscapeKeyDown={(e) => {
          if (createdKey && !acknowledged) e.preventDefault();
        }}
      >
        {!createdKey ? (
          <>
            <DialogHeader>
              <DialogTitle>Generate API key</DialogTitle>
              <DialogDescription>
                Create a new API key for your application to send metrics.
              </DialogDescription>
            </DialogHeader>

            <Form {...form}>
              <form
                onSubmit={form.handleSubmit(onSubmit)}
                className="space-y-4"
              >
                <FormField
                  control={form.control}
                  name="name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Key name</FormLabel>
                      <FormControl>
                        <Input placeholder="Production server" {...field} />
                      </FormControl>
                      <FormDescription>
                        A label to identify this key (e.g., environment or
                        service name).
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="expires_at"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Expiration date (optional)</FormLabel>
                      <FormControl>
                        <Input
                          type="date"
                          min={format(new Date(), "yyyy-MM-dd")}
                          {...field}
                          value={field.value ?? ""}
                          onChange={(e) =>
                            field.onChange(e.target.value || null)
                          }
                        />
                      </FormControl>
                      <FormDescription>
                        Leave blank for no expiration.
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
                        Generating…
                      </>
                    ) : (
                      "Generate"
                    )}
                  </Button>
                </DialogFooter>
              </form>
            </Form>
          </>
        ) : (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Key className="h-4 w-4 text-primary" />
                Your API key
              </DialogTitle>
              <DialogDescription>
                Copy this key now. It will not be shown again.
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4">
              {/* Warning banner */}
              <div className="flex gap-3 p-3 rounded-lg bg-amber-50 border border-amber-200">
                <AlertCircle className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />
                <p className="text-sm text-amber-800">
                  Save this key securely. Once you close this dialog, you{" "}
                  <strong>cannot</strong> retrieve it again. If lost, generate a
                  new key.
                </p>
              </div>

              {/* Key display */}
              <div className="space-y-2">
                <p className="text-xs font-medium text-muted-foreground">
                  {createdKey.name}
                </p>
                <div className="flex items-center gap-2 p-3 rounded-md bg-muted border border-border">
                  <code className="flex-1 text-sm font-mono break-all text-foreground">
                    {createdKey.key}
                  </code>
                  <CopyButton value={createdKey.key} />
                </div>
              </div>
            </div>

            <DialogFooter>
              <Button onClick={handleDone} className="w-full">
                I&apos;ve copied the key
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
