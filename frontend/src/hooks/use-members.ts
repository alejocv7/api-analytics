import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { queryKeys } from "@/lib/query-keys";
import type {
  InviteMemberRequest,
  Member,
  PaginatedResponse,
  UpdateMemberRoleRequest,
} from "@/types/api";

export function useMembers(projectKey: string) {
  return useQuery({
    queryKey: queryKeys.projects.members(projectKey),
    queryFn: () =>
      apiClient.get<PaginatedResponse<Member>>(
        `/projects/${projectKey}/members`,
        { page: 1, page_size: 50 },
      ),
    enabled: Boolean(projectKey),
  });
}

export function useInviteMember(projectKey: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: InviteMemberRequest) =>
      apiClient.post<Member>(`/projects/${projectKey}/members`, data),
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
