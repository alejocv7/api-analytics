"use client";

import { useState } from "react";
import { toast } from "sonner";
import { MoreHorizontal, Trash2, Users } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { RoleBadge } from "@/components/shared/role-badge";
import { EmptyState } from "@/components/shared/empty-state";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { InviteMemberDialog } from "./invite-member-dialog";
import { useMembers, useUpdateMemberRole, useRemoveMember } from "@/hooks/use-members";
import { formatDate } from "@/lib/utils";
import type { Member, ProjectRole } from "@/types/api";
import { useUser } from "@/hooks/use-user";

function getInitials(name: string): string {
  return name.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2);
}

interface MemberRowProps {
  member: Member;
  projectKey: string;
  isOwner: boolean;
  currentUserId?: string;
}

function MemberRow({ member, projectKey, isOwner, currentUserId }: MemberRowProps) {
  const [removeOpen, setRemoveOpen] = useState(false);
  const updateRole = useUpdateMemberRole(projectKey, member.user_id);
  const removeMember = useRemoveMember(projectKey, member.user_id);

  const isSelf = member.user_id === currentUserId;
  const isProjectOwner = member.role === "owner";
  const canManage = isOwner && !isProjectOwner && !isSelf;

  async function handleRoleChange(role: string) {
    try {
      await updateRole.mutateAsync({ role: role as "member" | "viewer" });
      toast.success("Role updated");
    } catch {
      toast.error("Failed to update role");
    }
  }

  async function handleRemove() {
    try {
      await removeMember.mutateAsync();
      toast.success(`${member.full_name} removed from project`);
      setRemoveOpen(false);
    } catch {
      toast.error("Failed to remove member");
    }
  }

  return (
    <div className="flex items-center justify-between py-3 border-b border-border last:border-0">
      <div className="flex items-center gap-3 min-w-0">
        <Avatar className="h-8 w-8 shrink-0">
          <AvatarFallback className="text-xs bg-primary/10 text-primary font-medium">
            {getInitials(member.full_name)}
          </AvatarFallback>
        </Avatar>
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium truncate">{member.full_name}</span>
            {isSelf && (
              <span className="text-xs text-muted-foreground">(you)</span>
            )}
          </div>
          <p className="text-xs text-muted-foreground truncate">{member.email}</p>
        </div>
      </div>

      <div className="flex items-center gap-3 shrink-0">
        <span className="text-xs text-muted-foreground hidden sm:block">
          Joined {formatDate(member.joined_at)}
        </span>

        {canManage ? (
          <Select value={member.role} onValueChange={handleRoleChange}>
            <SelectTrigger className="h-7 w-24 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="member">Member</SelectItem>
              <SelectItem value="viewer">Viewer</SelectItem>
            </SelectContent>
          </Select>
        ) : (
          <RoleBadge role={member.role} />
        )}

        {canManage && (
          <>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-7 w-7">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem
                  className="text-destructive focus:text-destructive"
                  onClick={() => setRemoveOpen(true)}
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Remove member
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            <ConfirmDialog
              open={removeOpen}
              onOpenChange={setRemoveOpen}
              title="Remove member"
              description={`Remove ${member.full_name} from this project? They will lose access immediately.`}
              confirmLabel="Remove"
              isDestructive
              isLoading={removeMember.isPending}
              onConfirm={handleRemove}
            />
          </>
        )}
      </div>
    </div>
  );
}

interface MembersTabProps {
  projectKey: string;
  isOwner: boolean;
}

export function MembersTab({ projectKey, isOwner }: MembersTabProps) {
  const { data, isLoading } = useMembers(projectKey);
  const { user } = useUser();

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="flex items-center gap-3">
            <Skeleton className="h-8 w-8 rounded-full" />
            <div className="space-y-1 flex-1">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-3 w-48" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  const members = data?.items ?? [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold">Team members</h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            {members.length} {members.length === 1 ? "member" : "members"}
          </p>
        </div>
        {isOwner && <InviteMemberDialog projectKey={projectKey} />}
      </div>

      {members.length === 0 ? (
        <EmptyState
          icon={Users}
          title="No team members"
          description="Invite colleagues to collaborate on this project."
          action={isOwner ? <InviteMemberDialog projectKey={projectKey} /> : undefined}
        />
      ) : (
        <div className="rounded-lg border border-border px-4">
          {members.map((member) => (
            <MemberRow
              key={member.user_id}
              member={member}
              projectKey={projectKey}
              isOwner={isOwner}
              currentUserId={user?.id}
            />
          ))}
        </div>
      )}
    </div>
  );
}
