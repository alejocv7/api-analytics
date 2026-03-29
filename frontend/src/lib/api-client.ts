import { API_URL } from "@/lib/constants";
import type { ApiError } from "@/types/api";

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

  let response: Response;
  try {
    response = await fetch(url.toString(), {
      ...rest,
      headers,
      credentials: "include",
      body: body
        ? isFormData
          ? (body as URLSearchParams)
          : JSON.stringify(body)
        : undefined,
    });
  } catch (err) {
    console.error(
      `[api] Network error on ${options.method ?? "GET"} ${path}:`,
      err,
    );
    throw err;
  }

  if (!response.ok) {
    if (
      response.status === 401 &&
      typeof window !== "undefined" &&
      !path.startsWith("/auth/")
    ) {
      window.dispatchEvent(new Event("auth:session-expired"));
    }
    const apiError = await parseError(response);
    console.error(
      `[api] ${options.method ?? "GET"} ${path} → ${response.status}:`,
      apiError.message,
      apiError.details ?? "",
    );
    throw apiError;
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export const apiClient = {
  get: <T>(path: string, params?: RequestOptions["params"]) =>
    request<T>(path, { method: "GET", params }),

  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body }),

  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PATCH", body }),

  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PUT", body }),

  delete: <T = void>(path: string) => request<T>(path, { method: "DELETE" }),
};
