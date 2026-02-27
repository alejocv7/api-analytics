"use client";

import { useState } from "react";
import { toast } from "sonner";
import { AlertCircle, Key, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { CopyButton } from "@/components/shared/copy-button";
import { useRotateApiKey } from "@/hooks/use-api-keys";
import type { ApiKey, ApiKeyCreateResponse } from "@/types/api";

interface RotateKeyDialogProps {
  projectKey: string;
  apiKey: ApiKey;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function RotateKeyDialog({
  projectKey,
  apiKey,
  open,
  onOpenChange,
}: RotateKeyDialogProps) {
  const [newKey, setNewKey] = useState<ApiKeyCreateResponse | null>(null);
  const rotateKey = useRotateApiKey(projectKey, apiKey.id);

  async function handleRotate() {
    try {
      const result = await rotateKey.mutateAsync();
      setNewKey(result);
    } catch {
      toast.error("Failed to rotate API key");
    }
  }

  function handleClose() {
    if (newKey) {
      toast.success("Key rotated. Old key has been deactivated.");
    }
    setNewKey(null);
    onOpenChange(false);
  }

  return (
    <Dialog open={open} onOpenChange={(next) => {
      if (!next && newKey) { handleClose(); return; }
      if (!next) onOpenChange(false);
    }}>
      <DialogContent
        className="sm:max-w-md"
        onInteractOutside={(e) => { if (newKey) e.preventDefault(); }}
        onEscapeKeyDown={(e) => { if (newKey) e.preventDefault(); }}
      >
        {!newKey ? (
          <>
            <DialogHeader>
              <DialogTitle>Rotate API key</DialogTitle>
              <DialogDescription>
                This will create a new key and immediately deactivate{" "}
                <strong>{apiKey.name}</strong>. Any applications using the old
                key will stop working.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button
                variant="destructive"
                onClick={handleRotate}
                disabled={rotateKey.isPending}
              >
                {rotateKey.isPending ? (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    Rotating…
                  </>
                ) : (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Rotate key
                  </>
                )}
              </Button>
            </DialogFooter>
          </>
        ) : (
          <>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Key className="h-4 w-4 text-primary" />
                New API key
              </DialogTitle>
              <DialogDescription>
                Copy this key now. It will not be shown again.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="flex gap-3 p-3 rounded-lg bg-amber-50 border border-amber-200">
                <AlertCircle className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />
                <p className="text-sm text-amber-800">
                  The old key has been deactivated. Update your applications
                  with the new key below.
                </p>
              </div>
              <div className="flex items-center gap-2 p-3 rounded-md bg-muted border border-border">
                <code className="flex-1 text-sm font-mono break-all text-foreground">
                  {newKey.key}
                </code>
                <CopyButton value={newKey.key} />
              </div>
            </div>
            <DialogFooter>
              <Button onClick={handleClose} className="w-full">
                I&apos;ve copied the key
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
