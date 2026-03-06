"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Key, Power, RefreshCw, Trash2 } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Card,
  CardContent,
  CardHeader,
} from "@/components/ui/card";
import { CreateApiKeyDialog } from "./create-api-key-dialog";
import { SearchableCardHeader } from "./searchable-card-header";
import { RotateKeyDialog } from "./rotate-key-dialog";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { EmptyState } from "@/components/shared/empty-state";
import { StatusBadge } from "@/components/shared/status-badge";
import {
  useApiKeys,
  useDeleteApiKey,
  useUpdateApiKey,
} from "@/hooks/use-api-keys";
import { cn, formatDate, formatNumber, maskApiKey } from "@/lib/utils";
import type { ApiKey } from "@/types/api";

interface ApiKeysTabProps {
  projectKey: string;
  isOwner: boolean;
}

interface ApiKeyRowActionsProps {
  projectKey: string;
  apiKey: ApiKey;
  isExpired: boolean;
}

function ApiKeyRowActions({
  projectKey,
  apiKey,
  isExpired,
}: ApiKeyRowActionsProps) {
  const [rotateOpen, setRotateOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const deleteKey = useDeleteApiKey(projectKey, apiKey.id);
  const updateKey = useUpdateApiKey(projectKey, apiKey.id);

  async function handleDelete() {
    try {
      await deleteKey.mutateAsync();
      toast.success("API key deleted");
      setDeleteOpen(false);
    } catch (error) {
      toast.error("Failed to delete key", {
        description: error instanceof Error ? error.message : "Unknown error",
      });
    }
  }

  async function handleToggleActive() {
    try {
      await updateKey.mutateAsync({ is_active: !apiKey.is_active });
      toast.success(
        apiKey.is_active ? "API key deactivated" : "API key activated",
      );
    } catch (error) {
      toast.error("Failed to update key", {
        description: error instanceof Error ? error.message : "Unknown error",
      });
    }
  }

  return (
    <>
      <div className="flex items-center gap-1 justify-end">
        {!isExpired && (
          <Button
            variant="ghost"
            size="icon"
            className={cn("h-7 w-7", apiKey.is_active ? "text-muted-foreground hover:text-amber-500" : "text-amber-500 hover:text-foreground")}
            onClick={handleToggleActive}
            disabled={updateKey.isPending}
            title={apiKey.is_active ? "Deactivate key" : "Activate key"}
          >
            <Power className="h-3.5 w-3.5" />
          </Button>
        )}
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7 text-muted-foreground hover:text-foreground"
          onClick={() => setRotateOpen(true)}
          title="Rotate key"
        >
          <RefreshCw className="h-3.5 w-3.5" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7 text-muted-foreground hover:text-destructive"
          onClick={() => setDeleteOpen(true)}
          title="Delete key"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </Button>
      </div>

      <RotateKeyDialog
        projectKey={projectKey}
        apiKey={apiKey}
        open={rotateOpen}
        onOpenChange={setRotateOpen}
      />

      <ConfirmDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        title="Delete API key"
        description={`Permanently delete "${apiKey.name}"? This cannot be undone. Any applications using this key will stop working immediately.`}
        confirmLabel="Delete"
        isDestructive
        isLoading={deleteKey.isPending}
        onConfirm={handleDelete}
      />
    </>
  );
}

export function ApiKeysTab({ projectKey, isOwner }: ApiKeysTabProps) {
  const { data, isLoading } = useApiKeys(projectKey);
  const [search, setSearch] = useState("");

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-24" />
          <Skeleton className="h-4 w-40" />
        </CardHeader>
        <CardContent className="space-y-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </CardContent>
      </Card>
    );
  }

  const allKeys = data?.items ?? [];
  const keys = search
    ? allKeys.filter(
        (k) =>
          k.name.toLowerCase().includes(search.toLowerCase()) ||
          k.key_prefix.toLowerCase().includes(search.toLowerCase()),
      )
    : allKeys;

  return (
    <Card className="pb-0">
      <SearchableCardHeader
        title="API Keys"
        description="Manage your API keys"
        search={{ value: search, onChange: setSearch, placeholder: "Search keys…" }}
        action={isOwner && <CreateApiKeyDialog projectKey={projectKey} />}
      />

      <CardContent className="p-0">
        {allKeys.length === 0 ? (
          <div className="px-6 pb-6">
            <EmptyState
              icon={Key}
              title="No API keys"
              description="Generate an API key to start sending metrics from your applications."
              action={
                isOwner ? (
                  <CreateApiKeyDialog projectKey={projectKey} />
                ) : undefined
              }
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="border-t border-border bg-muted/50">
                  <TableHead className="pl-5">Name</TableHead>
                  <TableHead>Key</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Requests</TableHead>
                  <TableHead>Expires</TableHead>
                  {isOwner && <TableHead className="pr-5" />}
                </TableRow>
              </TableHeader>
              <TableBody>
                {keys.length === 0 ? (
                  <TableRow>
                    <TableCell
                      colSpan={isOwner ? 7 : 6}
                      className="text-center text-sm text-muted-foreground py-8"
                    >
                      No keys match your search
                    </TableCell>
                  </TableRow>
                ) : (
                  keys.map((key) => {
                    const isExpired =
                      key.expires_at != null &&
                      new Date(key.expires_at) < new Date();

                    return (
                      <TableRow key={key.id} className="hover:bg-muted/50">
                        <TableCell className="pl-5">
                          <div className="flex items-center gap-2">
                            <Key className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                            <span className="text-sm font-medium">
                              {key.name}
                            </span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <code className="text-xs font-mono text-teal-600 bg-teal-50 px-1.5 py-0.5 rounded">
                            {maskApiKey(key.key_prefix)}
                          </code>
                        </TableCell>
                        <TableCell>
                          {isExpired ? (
                            <StatusBadge status="expired" />
                          ) : (
                            <StatusBadge
                              status={key.is_active ? "active" : "inactive"}
                            />
                          )}
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {formatDate(key.created_at)}
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {formatNumber(key.total_requests)}
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {key.expires_at
                            ? formatDate(key.expires_at)
                            : "Never"}
                        </TableCell>
                        {isOwner && (
                          <TableCell>
                            <ApiKeyRowActions
                              projectKey={projectKey}
                              apiKey={key}
                              isExpired={isExpired}
                            />
                          </TableCell>
                        )}
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
