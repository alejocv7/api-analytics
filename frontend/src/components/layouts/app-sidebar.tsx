"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  BarChart3,
  ChartArea,
  ChevronDown,
  FolderKanban,
  Moon,
  PanelLeftClose,
  PanelLeftOpen,
  Settings,
  Sun,
} from "lucide-react";
import { useTheme } from "next-themes";

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
import { useProjects, useProject } from "@/hooks/use-projects";
import { useActiveProject } from "@/providers/active-project-provider";
import { cn, getInitials } from "@/lib/utils";

export function AppSidebar() {
  const pathname = usePathname();
  const { open, toggleSidebar, isMobile, setOpenMobile, breakpoint, setOpen } =
    useSidebar();
  const { resolvedTheme, setTheme } = useTheme();
  const darkMode = resolvedTheme === "dark";
  const [themeHovered, setThemeHovered] = useState(false);

  // Derive which icon to show: current icon, or next-theme icon while hovering.
  // Reset hovered on click so the icon reflects the new theme immediately.
  const showSun = darkMode === themeHovered; // light+idle OR dark+hovered
  const showMoon = darkMode !== themeHovered; // dark+idle OR light+hovered

  const [projectSwitcherOpen, setProjectSwitcherOpen] = useState(false);
  const router = useRouter();

  // Auto-close on navigation: mobile closes the sheet, md closes the overlay.
  useEffect(() => {
    if (isMobile) {
      setOpenMobile(false);
    } else if (breakpoint === "md") {
      setOpen(false);
    }
  }, [pathname, isMobile, breakpoint, setOpenMobile, setOpen]);

  const projectKeyMatch = pathname.match(/^\/projects\/([^/]+)/);
  const currentPathKey = projectKeyMatch?.[1] ?? "";

  const { projectKey, setProjectKey } = useActiveProject();
  // Persist the last active project key so sidebar nav stays visible
  // when navigating to /projects (projects list).
  useEffect(() => {
    if (currentPathKey) setProjectKey(currentPathKey);
  }, [currentPathKey, setProjectKey]);

  const { data: projectsData } = useProjects(1, 50);
  const { data: currentProject } = useProject(projectKey);

  const projects = projectsData?.items ?? [];

  return (
    <Sidebar
      variant={isMobile ? "floating" : "inset"}
      collapsible="icon"
      className="absolute"
    >
      <SidebarHeader>
        {/* Brand — doubles as sidebar collapse toggle */}
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              size="lg"
              onClick={toggleSidebar}
              tooltip={open || isMobile ? "Collapse sidebar" : "Expand sidebar"}
              className="group/brand"
            >
              <div className="relative flex items-center justify-center w-8 h-8 rounded-lg bg-primary shrink-0">
                <BarChart3 className="h-4 w-4 text-sidebar-primary-foreground transition-opacity duration-150 group-hover/brand:opacity-0" />
                <span className="absolute inset-0 flex items-center justify-center opacity-0 transition-opacity duration-150 group-hover/brand:opacity-100">
                  {open || isMobile ? (
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
                  className="ring-1 ring-sidebar-border bg-sidebar-foreground/10 hover:bg-sidebar-foreground/20 px-4 py-2 min-h-14 h-auto"
                >
                  {!open && (
                    <Avatar className="h-8 w-8 shrink-0">
                      <AvatarFallback className="text-xs bg-sidebar-primary/30 text-sidebar-primary-foreground font-medium">
                        {getInitials(
                          currentProject?.name ?? (projectKey ? "…" : "?"),
                        )}
                      </AvatarFallback>
                    </Avatar>
                  )}

                  <div className="flex-1 min-w-0 text-left">
                    <span className="text-2xs font-semibold tracking-wider opacity-50 block leading-none mb-1">
                      Current Project
                    </span>
                    <span className="text-sm font-semibold line-clamp-2 leading-snug">
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
                        <span className="block wrap-break-word leading-snug">
                          {project.name}
                        </span>
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
                    <ChartArea className="h-4 w-4" />
                    <span>Dashboard</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroup>
        )}

        {/* Manage group */}
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

      {/* Dark mode toggle — click to switch, hover previews the next theme */}
      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              onClick={() => {
                setThemeHovered(false);
                setTheme(darkMode ? "light" : "dark");
              }}
              onMouseEnter={() => setThemeHovered(true)}
              onMouseLeave={() => setThemeHovered(false)}
              tooltip={
                darkMode ? "Switch to light mode" : "Switch to dark mode"
              }
            >
              <span className="relative h-4 w-4 shrink-0">
                <Sun
                  className={cn(
                    "absolute inset-0 h-4 w-4 text-amber-500 transition-all duration-200",
                    showSun
                      ? "opacity-100 scale-100 rotate-0"
                      : "opacity-0 scale-0 rotate-90",
                  )}
                />
                <Moon
                  className={cn(
                    "absolute inset-0 h-4 w-4 text-blue-400 transition-all duration-200",
                    showMoon
                      ? "opacity-100 scale-100 rotate-0"
                      : "opacity-0 scale-0 -rotate-90",
                  )}
                />
              </span>
              <span>{showSun ? "Light mode" : "Dark mode"}</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>

      <SidebarRail className="hover:after:bg-transparent" />
    </Sidebar>
  );
}
