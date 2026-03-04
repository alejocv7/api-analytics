import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { queryKeys } from "@/lib/query-keys";
import type {
  ApiKey,
  ApiKeyCreateResponse,
  CreateApiKeyRequest,
  UpdateApiKeyRequest,
  PaginatedResponse,
} from "@/types/api";

export function useApiKeys(projectKey: string, page = 1) {
  return useQuery({
    queryKey: queryKeys.projects.apiKeys(projectKey),
    queryFn: () =>
      apiClient.get<PaginatedResponse<ApiKey>>(
        `/projects/${projectKey}/api-keys`,
        { page, page_size: 20 },
      ),
    enabled: Boolean(projectKey),
  });
}

export function useCreateApiKey(projectKey: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateApiKeyRequest) =>
      apiClient.post<ApiKeyCreateResponse>(
        `/projects/${projectKey}/api-keys`,
        data,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.projects.apiKeys(projectKey),
      });
    },
  });
}

export function useUpdateApiKey(projectKey: string, keyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: UpdateApiKeyRequest) =>
      apiClient.patch<ApiKey>(
        `/projects/${projectKey}/api-keys/${keyId}`,
        data,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.projects.apiKeys(projectKey),
      });
    },
  });
}

export function useRotateApiKey(projectKey: string, keyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiClient.post<ApiKeyCreateResponse>(
        `/projects/${projectKey}/api-keys/${keyId}/rotate`,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.projects.apiKeys(projectKey),
      });
    },
  });
}

export function useDeleteApiKey(projectKey: string, keyId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiClient.delete(`/projects/${projectKey}/api-keys/${keyId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.projects.apiKeys(projectKey),
      });
    },
  });
}
