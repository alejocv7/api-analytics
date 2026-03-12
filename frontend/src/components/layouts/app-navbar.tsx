"use client";

import { useRef } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { LogOut, Menu, User } from "lucide-react";
import { toast } from "sonner";

import { useSidebar } from "@/components/ui/sidebar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { useUser } from "@/hooks/use-user";
import { useProject } from "@/hooks/use-projects";
import { getInitials } from "@/lib/utils";
import { StatusBadge } from "@/components/shared/status-badge";

export function AppNavbar() {
  const pathname = usePathname();
  const router = useRouter();
  const { toggleSidebar } = useSidebar();
  const { user, logout } = useUser();

  // Mirror the project-key resolution logic from AppSidebar so the navbar
  // always shows the correct project name even when on /projects list page.
  const projectKeyMatch = pathname.match(/^\/projects\/([^/]+)/);
  const currentPathKey = projectKeyMatch?.[1] ?? "";
  const lastProjectKeyRef = useRef(currentPathKey);
  if (currentPathKey) lastProjectKeyRef.current = currentPathKey;
  const projectKey = lastProjectKeyRef.current;

  const { data: currentProject } = useProject(projectKey);

  async function handleLogout() {
    try {
      await logout();
      router.push("/login");
    } catch {
      toast.error("Failed to log out. Please try again.");
    }
  }

  return (
    <header className="flex h-14 shrink-0 items-center gap-3 border-b px-4">
      {/* Mobile hamburger — hidden at md and above */}
      <Button
        variant="ghost"
        size="icon"
        className="md:hidden"
        onClick={toggleSidebar}
        aria-label="Toggle navigation"
      >
        <Menu className="h-5 w-5" />
      </Button>

      {/* Current project name + live status dot */}
      <div className="flex flex-1 justify-center">
        {currentProject && (
          <div className="flex items-center gap-3 min-w-0">
            <span className="truncate text-base font-semibold">
              {currentProject.name}
            </span>
            <StatusBadge
              status={currentProject.is_active ? "active" : "inactive"}
              dotOnly
            />
          </div>
        )}
      </div>

      {/* User avatar dropdown */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon" className="rounded-full shrink-0">
            <Avatar className="h-8 w-8">
              <AvatarFallback className="bg-primary/10 text-xs font-medium">
                {user ? getInitials(user.full_name) : "?"}
              </AvatarFallback>
            </Avatar>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56">
          {user && (
            <>
              <div className="px-2 py-1.5">
                <p className="text-sm font-medium leading-none">
                  {user.full_name}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  {user.email}
                </p>
              </div>
              <DropdownMenuSeparator />
            </>
          )}
          <DropdownMenuItem asChild>
            <Link href="/profile">
              <User className="mr-2 h-4 w-4" />
              Profile
            </Link>
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            className="text-destructive focus:text-destructive focus:bg-destructive/10"
            onClick={handleLogout}
          >
            <LogOut className="mr-2 h-4 w-4" />
            Log out
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </header>
  );
}
