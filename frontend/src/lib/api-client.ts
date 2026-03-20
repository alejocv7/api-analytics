import { API_URL } from "@/lib/constants";
import type { ApiError } from "@/types/api";

// Mutex to prevent concurrent token refresh races
let refreshPromise: Promise<void> | null = null;

async function refreshAccessToken(): Promise<void> {
  const response = await fetch(`${API_URL}/auth/refresh`, {
    method: "POST",
    credentials: "include",
  });

  if (!response.ok) {
    throw new ApiClientError("Session expired. Please log in again.", 401);
  }
  // New access_token and refresh_token cookies are set by the server response.
}

export class ApiClientError extends Error {
  constructor(
    message: string,
    public status: number,
    public details?: ApiError["details"],
    public requestId?: string | null,
  ) {
    super(message);
    this.name = "ApiClientError";
  }
}

async function parseError(response: Response): Promise<ApiClientError> {
  try {
    const body: ApiError = await response.json();
    return new ApiClientError(
      body.error ?? response.statusText,
      response.status,
      body.details,
      body.request_id,
    );
  } catch {
    return new ApiClientError(response.statusText, response.status);
  }
}

type RequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
  params?: Record<string, string | number | boolean | undefined | null>;
};

async function request<T>(
  path: string,
  options: RequestOptions = {},
  retry = true,
): Promise<T> {
  const { body, params, headers: extraHeaders, ...rest } = options;

  const url = new URL(`${API_URL}${path}`);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== null) {
        url.searchParams.set(key, String(value));
      }
    }
  }

  const headers: Record<string, string> = {
    ...(extraHeaders as Record<string, string>),
  };

  const isFormData = body instanceof URLSearchParams;
  if (body && !isFormData) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(url.toString(), {
    ...rest,
    headers,
    credentials: "include",
    body: body
      ? isFormData
        ? (body as URLSearchParams)
        : JSON.stringify(body)
      : undefined,
  });

  if (response.status === 401 && retry) {
    // Use mutex to prevent parallel refresh calls
    if (!refreshPromise) {
      refreshPromise = refreshAccessToken().finally(() => {
        refreshPromise = null;
      });
    }

    try {
      await refreshPromise;
    } catch (err) {
      throw err;
    }

    return request<T>(path, options, false);
  }

  if (!response.ok) {
    throw await parseError(response);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export const apiClient = {
  get: <T>(
    path: string,
    params?: RequestOptions["params"],
  ) => request<T>(path, { method: "GET", params }),

  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body }),

  postForm: <T>(path: string, data: Record<string, string>) => {
    const formData = new URLSearchParams(data);
    return request<T>(path, {
      method: "POST",
      body: formData,
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
  },

  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PATCH", body }),

  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PUT", body }),

  delete: <T = void>(path: string) => request<T>(path, { method: "DELETE" }),
};
