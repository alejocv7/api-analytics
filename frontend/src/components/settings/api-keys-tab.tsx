"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Key, RefreshCw, Trash2 } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { CreateApiKeyDialog } from "./create-api-key-dialog";
import { RotateKeyDialog } from "./rotate-key-dialog";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { PageHeader } from "@/components/layouts/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { SearchInput } from "@/components/shared/search-input";
import { StatusBadge } from "@/components/shared/status-badge";
import { useApiKeys, useDeleteApiKey } from "@/hooks/use-api-keys";
import { useProject } from "@/hooks/use-projects";
import { formatDate, formatNumber, maskApiKey } from "@/lib/utils";
import type { ApiKey } from "@/types/api";

interface ApiKeysTabProps {
  projectKey: string;
  isOwner: boolean;
}

interface ApiKeyRowActionsProps {
  projectKey: string;
  apiKey: ApiKey;
}

function ApiKeyRowActions({ projectKey, apiKey }: ApiKeyRowActionsProps) {
  const [rotateOpen, setRotateOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const deleteKey = useDeleteApiKey(projectKey, apiKey.id);

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

  return (
    <>
      <div className="flex items-center gap-1 justify-end">
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
  const { data: project } = useProject(projectKey);
  const [search, setSearch] = useState("");

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-full" />
        <div className="space-y-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      </div>
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
    <div className="space-y-4">
      <PageHeader
        title="API Keys"
        description="Manage your API keys"
        action={
          <div className="flex items-center gap-2">
            <SearchInput
              placeholder="Search keys…"
              value={search}
              onChange={setSearch}
            />
            {isOwner && <CreateApiKeyDialog projectKey={projectKey} />}
          </div>
        }
      />

      {allKeys.length === 0 ? (
        <EmptyState
          icon={Key}
          title="No API keys"
          description="Generate an API key to start sending metrics from your applications."
          action={
            isOwner ? <CreateApiKeyDialog projectKey={projectKey} /> : undefined
          }
        />
      ) : (
        <div className="rounded-lg border border-border overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/50">
                <TableHead className="text-xs font-medium text-muted-foreground uppercase tracking-wide pl-5">
                  Name
                </TableHead>
                <TableHead className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                  Key
                </TableHead>
                <TableHead className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                  Status
                </TableHead>
                <TableHead className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                  Created
                </TableHead>
                <TableHead className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                  Requests
                </TableHead>
                <TableHead className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                  Expires
                </TableHead>
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
                keys.map((key) => (
                  <TableRow key={key.id}>
                    <TableCell className="pl-4">
                      <div className="flex items-center gap-2">
                        <Key className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                        <span className="text-sm font-medium">{key.name}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <code className="text-xs font-mono text-teal-600 bg-teal-50 px-1.5 py-0.5 rounded">
                        {maskApiKey(key.key_prefix)}
                      </code>
                    </TableCell>
                    <TableCell>
                      {(() => {
                        const now = new Date();
                        const isExpired =
                          key.expires_at !== null &&
                          key.expires_at !== undefined &&
                          new Date(key.expires_at) < now;
                        if (isExpired) return <StatusBadge status="expired" />;
                        return (
                          <StatusBadge
                            status={key.is_active ? "active" : "inactive"}
                          />
                        );
                      })()}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatDate(key.created_at)}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatNumber(key.total_requests)}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {key.expires_at ? formatDate(key.expires_at) : "Never"}
                    </TableCell>
                    {isOwner && (
                      <TableCell>
                        <ApiKeyRowActions
                          projectKey={projectKey}
                          apiKey={key}
                        />
                      </TableCell>
                    )}
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
