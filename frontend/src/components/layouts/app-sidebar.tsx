"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, FolderKanban, User } from "lucide-react";

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from "@/components/ui/sidebar";
import { cn } from "@/lib/utils";
import { useUser } from "@/hooks/use-user";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

const navItems = [
  {
    href: "/dashboard",
    label: "Projects",
    icon: FolderKanban,
    exact: true,
  },
] as const;

function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

export function AppSidebar() {
  const pathname = usePathname();
  const { user } = useUser();

  return (
    <Sidebar variant="inset" collapsible="icon">
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild>
              <Link href="/dashboard" className="flex items-center gap-2">
                <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-primary shrink-0">
                  <BarChart3 className="h-4 w-4 text-primary-foreground" />
                </div>
                <span className="font-semibold text-sm tracking-tight">
                  API Analytics
                </span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarContent>
        <SidebarMenu>
          {navItems.map((item) => {
            const isActive = item.exact
              ? pathname === item.href
              : pathname.startsWith(item.href);
            return (
              <SidebarMenuItem key={item.href}>
                <SidebarMenuButton
                  asChild
                  isActive={isActive}
                  tooltip={item.label}
                >
                  <Link href={item.href}>
                    <item.icon
                      className={cn(
                        "h-4 w-4",
                        isActive ? "text-primary" : "text-muted-foreground",
                      )}
                    />
                    <span>{item.label}</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            );
          })}
        </SidebarMenu>
      </SidebarContent>

      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton asChild tooltip="Profile">
              <Link href="/profile" className="flex items-center gap-2">
                <Avatar className="h-6 w-6 shrink-0">
                  <AvatarFallback className="text-xs bg-primary/10 text-primary">
                    {user ? getInitials(user.full_name) : "?"}
                  </AvatarFallback>
                </Avatar>
                <span className="text-sm truncate">{user?.full_name}</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>
  );
}
