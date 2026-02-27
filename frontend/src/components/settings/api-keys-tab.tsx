"use client";

import { useState } from "react";
import { toast } from "sonner";
import { MoreHorizontal, RefreshCw, Trash2, XCircle } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { CreateApiKeyDialog } from "./create-api-key-dialog";
import { RotateKeyDialog } from "./rotate-key-dialog";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { EmptyState } from "@/components/shared/empty-state";
import {
  useApiKeys,
  useDeactivateApiKey,
  useDeleteApiKey,
} from "@/hooks/use-api-keys";
import { formatDate, formatRelative, formatNumber, maskApiKey } from "@/lib/utils";
import type { ApiKey } from "@/types/api";
import { Key } from "lucide-react";

interface ApiKeysTabProps {
  projectKey: string;
  isOwner: boolean;
}

function KeyStatusBadge({ apiKey }: { apiKey: ApiKey }) {
  const now = new Date();
  const isExpired =
    apiKey.expires_at !== null &&
    apiKey.expires_at !== undefined &&
    new Date(apiKey.expires_at) < now;

  if (isExpired) {
    return (
      <Badge variant="outline" className="bg-red-50 text-red-600 border-red-200 text-xs">
        Expired
      </Badge>
    );
  }
  if (!apiKey.is_active) {
    return (
      <Badge variant="outline" className="bg-slate-100 text-slate-500 border-slate-200 text-xs">
        Inactive
      </Badge>
    );
  }
  return (
    <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 text-xs">
      <span className="mr-1.5 inline-block h-1.5 w-1.5 rounded-full bg-green-500" />
      Active
    </Badge>
  );
}

interface ApiKeyRowActionsProps {
  projectKey: string;
  apiKey: ApiKey;
  isOwner: boolean;
}

function ApiKeyRowActions({ projectKey, apiKey, isOwner }: ApiKeyRowActionsProps) {
  const [rotateOpen, setRotateOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  const deactivate = useDeactivateApiKey(projectKey, apiKey.id);
  const deleteKey = useDeleteApiKey(projectKey, apiKey.id);

  async function handleDeactivate() {
    try {
      await deactivate.mutateAsync();
      toast.success("API key deactivated");
    } catch {
      toast.error("Failed to deactivate key");
    }
  }

  async function handleDelete() {
    try {
      await deleteKey.mutateAsync();
      toast.success("API key deleted");
      setDeleteOpen(false);
    } catch {
      toast.error("Failed to delete key");
    }
  }

  if (!isOwner) return null;

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon" className="h-8 w-8">
            <MoreHorizontal className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          {apiKey.is_active && (
            <DropdownMenuItem
              onClick={handleDeactivate}
              disabled={deactivate.isPending}
            >
              <XCircle className="mr-2 h-4 w-4" />
              Deactivate
            </DropdownMenuItem>
          )}
          <DropdownMenuItem onClick={() => setRotateOpen(true)}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Rotate
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            className="text-destructive focus:text-destructive"
            onClick={() => setDeleteOpen(true)}
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

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

  if (isLoading) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    );
  }

  const keys = data?.items ?? [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold">API Keys</h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            Keys used by your applications to send metrics.
          </p>
        </div>
        {isOwner && <CreateApiKeyDialog projectKey={projectKey} />}
      </div>

      {keys.length === 0 ? (
        <EmptyState
          icon={Key}
          title="No API keys"
          description="Generate an API key to start sending metrics from your applications."
          action={isOwner ? <CreateApiKeyDialog projectKey={projectKey} /> : undefined}
        />
      ) : (
        <div className="rounded-lg border border-border overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead className="text-xs pl-4">Name</TableHead>
                <TableHead className="text-xs">Prefix</TableHead>
                <TableHead className="text-xs">Status</TableHead>
                <TableHead className="text-xs">Requests</TableHead>
                <TableHead className="text-xs">Last used</TableHead>
                <TableHead className="text-xs">Expires</TableHead>
                {isOwner && <TableHead className="w-10" />}
              </TableRow>
            </TableHeader>
            <TableBody>
              {keys.map((key) => (
                <TableRow key={key.id}>
                  <TableCell className="pl-4 text-sm font-medium">
                    {key.name}
                  </TableCell>
                  <TableCell>
                    <code className="text-xs font-mono text-muted-foreground">
                      {maskApiKey(key.prefix)}
                    </code>
                  </TableCell>
                  <TableCell>
                    <KeyStatusBadge apiKey={key} />
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {formatNumber(key.total_requests)}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {key.last_used_at
                      ? formatRelative(key.last_used_at)
                      : "Never"}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {key.expires_at ? formatDate(key.expires_at) : "No expiry"}
                  </TableCell>
                  {isOwner && (
                    <TableCell>
                      <ApiKeyRowActions
                        projectKey={projectKey}
                        apiKey={key}
                        isOwner={isOwner}
                      />
                    </TableCell>
                  )}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
