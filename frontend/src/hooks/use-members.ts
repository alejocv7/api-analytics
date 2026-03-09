import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/providers/auth-provider";
import { apiClient } from "@/lib/api-client";
import { queryKeys } from "@/lib/query-keys";
import type {
  InviteMemberRequest,
  Member,
  PaginatedResponse,
  ProjectRole,
  UpdateMemberRoleRequest,
} from "@/types/api";

/** Returns the current user's role in the project, derived from the member list. */
export function useCurrentMemberRole(projectKey: string): {
  role: ProjectRole | null;
  isLoading: boolean;
} {
  const { user } = useAuth();
  const { data, isLoading } = useMembers(projectKey);

  if (!user || isLoading || !data) return { role: null, isLoading };

  const self = data.items.find((m) => m.user_id === user.id);
  return { role: self?.role ?? null, isLoading: false };
}

export function useMembers(projectKey: string) {
  return useQuery({
    queryKey: queryKeys.projects.members(projectKey),
    queryFn: () =>
      apiClient.get<PaginatedResponse<Member>>(
        `/projects/${projectKey}/members/`,
        { page: 1, page_size: 50 },
      ),
    enabled: Boolean(projectKey),
  });
}

export function useInviteMember(projectKey: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: InviteMemberRequest) =>
      apiClient.post<Member>(`/projects/${projectKey}/members/`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.projects.members(projectKey),
      });
    },
  });
}

export function useUpdateMemberRole(projectKey: string, memberId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: UpdateMemberRoleRequest) =>
      apiClient.patch<Member>(
        `/projects/${projectKey}/members/${memberId}`,
        data,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.projects.members(projectKey),
      });
    },
  });
}

export function useRemoveMember(projectKey: string, memberId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiClient.delete(`/projects/${projectKey}/members/${memberId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.projects.members(projectKey),
      });
    },
  });
}
