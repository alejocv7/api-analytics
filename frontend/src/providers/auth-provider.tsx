"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { apiClient, ApiClientError } from "@/lib/api-client";
import type { LoginRequest, User } from "@/types/api";

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
    // Tokens are in HttpOnly cookies — always attempt /users/me and let the
    // server (or the api-client refresh flow) determine auth state.
    try {
      const me = await apiClient.get<User>("/users/me");
      setUser(me);
    } catch (err) {
      if (err instanceof ApiClientError && err.status === 401) {
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
      // Login sets HttpOnly cookies and returns UserResponse directly.
      const me = await apiClient.postForm<User>("/auth/login", {
        username: credentials.username,
        password: credentials.password,
      });
      setUser(me);
    },
    [],
  );

  const logout = useCallback(async (): Promise<void> => {
    try {
      await apiClient.post("/auth/logout");
    } catch (err) {
      // 401 means the token is already invalid server-side — treat as success.
      // Any other error (network failure, 5xx) means the server didn't clear the
      // HttpOnly cookies, so the session is still technically active.
      if (!(err instanceof ApiClientError && err.status === 401)) {
        toast.warning(
          "Logout failed. Close your browser to fully end the session.",
        );
      }
    } finally {
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
