"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Trash2, Users } from "lucide-react";
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
import { Skeleton } from "@/components/ui/skeleton";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { EmptyState } from "@/components/shared/empty-state";
import { SearchInput } from "@/components/shared/search-input";
import { StatusBadge } from "@/components/shared/status-badge";
import { RoleBadge } from "@/components/shared/role-badge";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";
import { InviteMemberDialog } from "./invite-member-dialog";
import {
  useMembers,
  useUpdateMemberRole,
  useRemoveMember,
} from "@/hooks/use-members";
import { formatDate, getInitials } from "@/lib/utils";
import type { Member, ProjectRole } from "@/types/api";
import { useUser } from "@/hooks/use-user";

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
        <TableCell className="pl-5">
          <div className="flex items-center gap-3">
            <Avatar className="h-8 w-8 shrink-0">
              <AvatarFallback className="text-xs bg-sidebar-primary/30 text-sidebar-primary-foreground font-medium">
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
            <RoleBadge role={member.role} />
          )}
        </TableCell>

        {/* Status */}
        <TableCell>
          <StatusBadge status="active" className="h-5" />
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
  const { user } = useUser();
  const [search, setSearch] = useState("");

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-4 w-40" />
        </CardHeader>
        <CardContent className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3">
              <Skeleton className="h-8 w-8 rounded-full" />
              <div className="space-y-1 flex-1">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-3 w-48" />
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
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
    <Card className="pb-0">
      <CardHeader className="flex flex-row items-start justify-between gap-4">
        <div className="space-y-1">
          <CardTitle>Team Members</CardTitle>
          <CardDescription>Manage project access</CardDescription>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <SearchInput
            placeholder="Search members…"
            value={search}
            onChange={setSearch}
          />
          {isOwner && <InviteMemberDialog projectKey={projectKey} />}
        </div>
      </CardHeader>

      <CardContent className="p-0">
        {allMembers.length === 0 ? (
          <div className="px-6 pb-6">
            <EmptyState
              icon={Users}
              title="No team members"
              description="Invite colleagues to collaborate on this project."
              action={
                isOwner ? (
                  <InviteMemberDialog projectKey={projectKey} />
                ) : undefined
              }
            />
          </div>
        ) : (
          <div className="overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="border-t border-border hover:bg-transparent bg-muted/50">
                  <TableHead className="text-xs font-medium text-muted-foreground uppercase tracking-wide pl-5">
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
      </CardContent>
    </Card>
  );
}
