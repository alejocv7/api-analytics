import { useAuth } from "@/providers/auth-provider";

export function useUser() {
  const { user, isLoading, isAuthenticated, logout } = useAuth();
  return { user, isLoading, isAuthenticated, logout };
}
