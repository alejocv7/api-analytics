import {
  useQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { queryKeys } from "@/lib/query-keys";
import type {
  Project,
  CreateProjectRequest,
  UpdateProjectRequest,
  PaginatedResponse,
} from "@/types/api";

export function useProjects(page = 1, pageSize = 20) {
  return useQuery({
    queryKey: queryKeys.projects.list({ page, page_size: pageSize }),
    queryFn: () =>
      apiClient.get<PaginatedResponse<Project>>("/projects", {
        page,
        page_size: pageSize,
      }),
  });
}

export function useProject(projectKey: string) {
  return useQuery({
    queryKey: queryKeys.projects.detail(projectKey),
    queryFn: () => apiClient.get<Project>(`/projects/${projectKey}`),
    enabled: Boolean(projectKey),
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateProjectRequest) =>
      apiClient.post<Project>("/projects", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.all() });
    },
  });
}

export function useUpdateProject(projectKey: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: UpdateProjectRequest) =>
      apiClient.patch<Project>(`/projects/${projectKey}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.all() });
      queryClient.invalidateQueries({
        queryKey: queryKeys.projects.detail(projectKey),
      });
    },
  });
}

export function useDeleteProject(projectKey: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiClient.delete(`/projects/${projectKey}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.all() });
    },
  });
}
