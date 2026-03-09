"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { useQueryClient } from "@tanstack/react-query";
import { apiClient, ApiClientError } from "@/lib/api-client";
import {
  clearTokens,
  getAccessToken,
  setTokens,
} from "@/lib/auth";
import type { LoginRequest, TokenResponse, User } from "@/types/api";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  refetchUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const queryClient = useQueryClient();

  const fetchUser = useCallback(async (): Promise<void> => {
    if (!getAccessToken()) {
      setIsLoading(false);
      return;
    }
    try {
      const me = await apiClient.get<User>("/users/me");
      setUser(me);
    } catch (err) {
      if (err instanceof ApiClientError && err.status === 401) {
        clearTokens();
        setUser(null);
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const login = useCallback(
    async (credentials: LoginRequest): Promise<void> => {
      const tokens = await apiClient.postForm<TokenResponse>("/auth/login", {
        username: credentials.username,
        password: credentials.password,
      });
      setTokens(tokens.access_token, tokens.refresh_token);
      const me = await apiClient.get<User>("/users/me");
      setUser(me);
    },
    [],
  );

  const logout = useCallback(async (): Promise<void> => {
    try {
      await apiClient.post("/auth/logout");
    } catch {
      // Best-effort logout; clear tokens regardless
    } finally {
      clearTokens();
      setUser(null);
      queryClient.clear();
    }
  }, [queryClient]);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: user !== null,
        login,
        logout,
        refetchUser: fetchUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
