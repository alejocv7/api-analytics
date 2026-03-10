"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  BarChart3,
  ChevronDown,
  ChevronUp,
  FolderKanban,
  LogOut,
  Moon,
  PanelLeftClose,
  PanelLeftOpen,
  Settings,
  Sun,
  User,
} from "lucide-react";
import { useTheme } from "next-themes";
import { toast } from "sonner";

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
  useSidebar,
} from "@/components/ui/sidebar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { useUser } from "@/hooks/use-user";
import { useProjects, useProject } from "@/hooks/use-projects";
import { cn, getInitials } from "@/lib/utils";

export function AppSidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useUser();
  const { open, toggleSidebar, isMobile, setOpenMobile } = useSidebar();

  const [projectSwitcherOpen, setProjectSwitcherOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const { theme, setTheme, resolvedTheme } = useTheme();
  const darkMode = resolvedTheme === "dark";

  useEffect(() => {
    setOpenMobile(false);
  }, [pathname, setOpenMobile]);

  const projectKeyMatch = pathname.match(/^\/projects\/([^/]+)/);
  const currentPathKey = projectKeyMatch?.[1] ?? "";

  // Persist the last active project key so sidebar nav stays visible
  // when navigating to /projects (projects list)
  const lastProjectKeyRef = useRef(currentPathKey);
  if (currentPathKey) lastProjectKeyRef.current = currentPathKey;
  const projectKey = lastProjectKeyRef.current;

  const { data: projectsData } = useProjects(1, 50);
  const { data: currentProject } = useProject(projectKey);

  const projects = projectsData?.items ?? [];

  function toggleDarkMode(enabled: boolean) {
    setTheme(enabled ? "dark" : "light");
  }

  async function handleLogout() {
    try {
      await logout();
      router.push("/login");
    } catch {
      toast.error("Failed to log out. Please try again.");
    }
  }

  return (
    <Sidebar
      variant="inset"
      collapsible="icon"
      side={isMobile ? "right" : "left"}
    >
      <SidebarHeader>
        {/* Brand — doubles as sidebar collapse toggle */}
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              size="lg"
              onClick={toggleSidebar}
              tooltip={open ? "Collapse sidebar" : "Expand sidebar"}
              className="group/brand"
            >
              <div className="relative flex items-center justify-center w-8 h-8 rounded-lg bg-primary shrink-0">
                <BarChart3 className="h-4 w-4 text-sidebar-primary-foreground transition-opacity duration-150 group-hover/brand:opacity-0" />
                <span className="absolute inset-0 flex items-center justify-center opacity-0 transition-opacity duration-150 group-hover/brand:opacity-100">
                  {open ? (
                    <PanelLeftClose className="h-4 w-4 text-sidebar-primary-foreground" />
                  ) : (
                    <PanelLeftOpen className="h-4 w-4 text-sidebar-primary-foreground" />
                  )}
                </span>
              </div>
              <span className="font-semibold text-sm tracking-tight">
                API Analytics
              </span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>

        {/* Project Switcher */}
        <SidebarMenu>
          <SidebarMenuItem>
            <Popover
              open={projectSwitcherOpen}
              onOpenChange={setProjectSwitcherOpen}
            >
              <PopoverTrigger asChild>
                <SidebarMenuButton
                  size="lg"
                  tooltip={currentProject?.name ?? "Switch project"}
                  className="ring-1 ring-sidebar-border bg-sidebar-accent/60 hover:bg-sidebar-accent"
                >
                  <Avatar className="h-8 w-8 shrink-0">
                    <AvatarFallback className="text-xs bg-sidebar-primary/30 text-sidebar-primary-foreground font-medium">
                      {getInitials(
                        currentProject?.name ?? (projectKey ? "…" : "?"),
                      )}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1 min-w-0 text-left">
                    <span className="text-2xs font-semibold tracking-wider opacity-50 block leading-none mb-1">
                      Current Project
                    </span>
                    <span className="text-sm font-semibold truncate block">
                      {currentProject?.name ??
                        (projectKey ? "Loading…" : "Select project")}
                    </span>
                  </div>
                  <ChevronDown className="h-4 w-4 shrink-0 opacity-50" />
                </SidebarMenuButton>
              </PopoverTrigger>
              <PopoverContent
                className="w-56 p-1"
                align="start"
                side="bottom"
                sideOffset={4}
              >
                {projects.length === 0 ? (
                  <p className="text-xs text-muted-foreground px-2 py-1.5">
                    No projects
                  </p>
                ) : (
                  <div className="space-y-0.5">
                    {projects.map((project) => (
                      <button
                        key={project.id}
                        className={cn(
                          "w-full text-left text-sm px-2 py-1.5 rounded-md transition-colors hover:bg-accent hover:text-accent-foreground",
                          project.project_key === projectKey &&
                            "bg-accent text-accent-foreground font-medium",
                        )}
                        onClick={() => {
                          setProjectSwitcherOpen(false);
                          router.push(
                            `/projects/${project.project_key}/dashboard`,
                          );
                        }}
                      >
                        <span className="truncate block">{project.name}</span>
                      </button>
                    ))}
                  </div>
                )}
              </PopoverContent>
            </Popover>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarContent>
        {/* Navigation group — shown whenever we have an active project */}
        {projectKey && (
          <SidebarGroup>
            <SidebarGroupLabel>Navigation</SidebarGroupLabel>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton
                  asChild
                  isActive={
                    pathname.startsWith("/projects/") &&
                    pathname.endsWith("/dashboard")
                  }
                  tooltip="Dashboard"
                >
                  <Link href={`/projects/${projectKey}/dashboard`}>
                    <BarChart3 className="h-4 w-4" />
                    <span>Dashboard</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroup>
        )}

        {/* General group */}
        <SidebarGroup>
          <SidebarGroupLabel>Manage</SidebarGroupLabel>
          <SidebarMenu>
            {projectKey && (
              <SidebarMenuItem>
                <SidebarMenuButton
                  asChild
                  isActive={pathname.includes("/settings")}
                  tooltip="Settings"
                >
                  <Link href={`/projects/${projectKey}/settings`}>
                    <Settings className="h-4 w-4" />
                    <span>Settings</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            )}
            <SidebarMenuItem>
              <SidebarMenuButton
                asChild
                isActive={pathname === "/projects"}
                tooltip="Projects"
              >
                <Link href="/projects">
                  <FolderKanban className="h-4 w-4" />
                  <span>Projects</span>
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <Popover open={userMenuOpen} onOpenChange={setUserMenuOpen}>
              <PopoverTrigger asChild>
                <SidebarMenuButton
                  size="lg"
                  tooltip={user?.full_name ?? "Account"}
                >
                  <Avatar className="h-8 w-8 shrink-0">
                    <AvatarFallback className="text-xs bg-sidebar-primary/30 text-sidebar-primary-foreground font-medium">
                      {user ? getInitials(user.full_name) : "?"}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1 min-w-0 text-left">
                    <span className="text-sm font-medium truncate block">
                      {user?.full_name}
                    </span>
                    <span className="text-xs opacity-60 truncate block">
                      {user?.email}
                    </span>
                  </div>
                  <ChevronUp className="h-4 w-4 shrink-0 opacity-50" />
                </SidebarMenuButton>
              </PopoverTrigger>
              <PopoverContent
                className="w-56 p-1.5"
                align="start"
                side="top"
                sideOffset={4}
              >
                <div className="space-y-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="w-full justify-start text-sm font-normal"
                    asChild
                    onClick={() => setUserMenuOpen(false)}
                  >
                    <Link href="/profile">
                      <User className="mr-2 h-4 w-4" />
                      Profile
                    </Link>
                  </Button>

                  <div className="flex items-center justify-between px-2 py-1.5 text-sm rounded-md hover:bg-accent hover:text-accent-foreground transition-colors">
                    <div className="flex items-center gap-2">
                      {darkMode ? (
                        <Moon className="h-4 w-4 text-primary" />
                      ) : (
                        <Sun className="h-4 w-4 text-amber-500" />
                      )}
                      <span>Dark Mode</span>
                    </div>
                    <Switch
                      checked={darkMode}
                      onCheckedChange={toggleDarkMode}
                      className="scale-75 origin-right"
                    />
                  </div>

                  <div className="my-1 h-px bg-border" />

                  <Button
                    variant="ghost"
                    size="sm"
                    className="w-full justify-start text-sm font-normal text-destructive hover:text-destructive hover:bg-destructive/10"
                    onClick={handleLogout}
                  >
                    <LogOut className="mr-2 h-4 w-4" />
                    Log out
                  </Button>
                </div>
              </PopoverContent>
            </Popover>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>
  );
}
