import { QueryClient } from "@tanstack/react-query";
import { ApiClientError } from "@/lib/api-client";

export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30 * 1000, // 30 seconds
        retry: (failureCount, error) => {
          if (error instanceof ApiClientError && error.status < 500) {
            return false; // don't retry 4xx errors
          }
          return failureCount < 2;
        },
      },
      mutations: {
        retry: false,
      },
    },
  });
}
