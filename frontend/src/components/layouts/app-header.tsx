"use client";

import { SidebarTrigger } from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";

interface AppHeaderProps {
  breadcrumb?: React.ReactNode;
}

export function AppHeader({ breadcrumb }: AppHeaderProps) {
  return (
    <div className="fixed top-3 right-3 z-50 md:hidden bg-background border border-border rounded-md shadow-sm">
      <SidebarTrigger />
    </div>
  );
}
