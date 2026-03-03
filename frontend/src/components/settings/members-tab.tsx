"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Search, Trash2, Users } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/shared/empty-state";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { InviteMemberDialog } from "./invite-member-dialog";
import { PageHeader } from "@/components/layouts/page-header";
import {
  useMembers,
  useUpdateMemberRole,
  useRemoveMember,
} from "@/hooks/use-members";
import { useProject } from "@/hooks/use-projects";
import { formatDate } from "@/lib/utils";
import type { Member, ProjectRole } from "@/types/api";
import { useUser } from "@/hooks/use-user";

function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

const ROLE_LABELS: Record<ProjectRole, string> = {
  owner: "Owner",
  member: "Member",
  viewer: "Viewer",
};

interface MemberRowProps {
  member: Member;
  projectKey: string;
  isOwner: boolean;
  currentUserId?: string;
}

function MemberRow({
  member,
  projectKey,
  isOwner,
  currentUserId,
}: MemberRowProps) {
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
    <>
      <TableRow>
        {/* Member */}
        <TableCell>
          <div className="flex items-center gap-3">
            <Avatar className="h-8 w-8 shrink-0">
              <AvatarFallback className="text-xs bg-indigo-100 text-indigo-700 font-medium">
                {getInitials(member.full_name)}
              </AvatarFallback>
            </Avatar>
            <div className="min-w-0">
              <span className="text-sm font-medium block truncate">
                {member.full_name}
                {isSelf && (
                  <span className="ml-1.5 text-xs text-muted-foreground font-normal">
                    (you)
                  </span>
                )}
              </span>
            </div>
          </div>
        </TableCell>

        {/* Email */}
        <TableCell>
          <span className="text-sm text-muted-foreground">{member.email}</span>
        </TableCell>

        {/* Role */}
        <TableCell>
          {canManage ? (
            <Select value={member.role} onValueChange={handleRoleChange}>
              <SelectTrigger className="h-7 w-28 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="member">Member</SelectItem>
                <SelectItem value="viewer">Viewer</SelectItem>
              </SelectContent>
            </Select>
          ) : (
            <Badge variant="outline" className="text-xs font-medium">
              {ROLE_LABELS[member.role]}
            </Badge>
          )}
        </TableCell>

        {/* Status */}
        <TableCell>
          <div className="flex items-center gap-1.5">
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-green-500" />
            <span className="text-sm text-muted-foreground">Active</span>
          </div>
        </TableCell>

        {/* Joined */}
        <TableCell>
          <span className="text-sm text-muted-foreground">
            {formatDate(member.joined_at)}
          </span>
        </TableCell>

        {/* Actions */}
        <TableCell>
          {canManage && (
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 text-muted-foreground hover:text-destructive"
              onClick={() => setRemoveOpen(true)}
              title="Remove member"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </Button>
          )}
        </TableCell>
      </TableRow>

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
  );
}

interface MembersTabProps {
  projectKey: string;
  isOwner: boolean;
}

export function MembersTab({ projectKey, isOwner }: MembersTabProps) {
  const { data, isLoading } = useMembers(projectKey);
  const { data: project } = useProject(projectKey);
  const { user } = useUser();
  const [search, setSearch] = useState("");

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-full" />
        <div className="space-y-2">
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
      </div>
    );
  }

  const allMembers = data?.items ?? [];
  const members = search
    ? allMembers.filter(
        (m) =>
          m.full_name.toLowerCase().includes(search.toLowerCase()) ||
          m.email.toLowerCase().includes(search.toLowerCase()),
      )
    : allMembers;

  return (
    <div className="space-y-4">
      <PageHeader
        title="Team Members"
        description="Manage project access"
        action={
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
              <Input
                placeholder="Search members…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-8 h-9 w-48 text-sm"
              />
            </div>
            {isOwner && <InviteMemberDialog projectKey={projectKey} />}
          </div>
        }
      />

      {allMembers.length === 0 ? (
        <EmptyState
          icon={Users}
          title="No team members"
          description="Invite colleagues to collaborate on this project."
          action={
            isOwner ? <InviteMemberDialog projectKey={projectKey} /> : undefined
          }
        />
      ) : (
        <div className="rounded-lg border border-border overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent bg-muted/30">
                <TableHead className="text-xs font-medium text-muted-foreground uppercase tracking-wide pl-4">
                  Member
                </TableHead>
                <TableHead className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                  Email
                </TableHead>
                <TableHead className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                  Role
                </TableHead>
                <TableHead className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                  Status
                </TableHead>
                <TableHead className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                  Joined
                </TableHead>
                <TableHead className="w-16" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {members.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={6}
                    className="text-center text-sm text-muted-foreground py-8"
                  >
                    No members match your search
                  </TableCell>
                </TableRow>
              ) : (
                members.map((member) => (
                  <MemberRow
                    key={member.user_id}
                    member={member}
                    projectKey={projectKey}
                    isOwner={isOwner}
                    currentUserId={user?.id}
                  />
                ))
              )}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
