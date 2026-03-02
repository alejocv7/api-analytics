"use client";

import { SidebarTrigger } from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";

interface AppHeaderProps {
  breadcrumb?: React.ReactNode;
}

export function AppHeader({ breadcrumb }: AppHeaderProps) {
  return (
    <header className="flex h-14 shrink-0 items-center gap-2 border-b border-border px-4">
      <SidebarTrigger className="-ml-1" />
      {breadcrumb && (
        <>
          <Separator orientation="vertical" className="h-4" />
          <div className="flex-1 min-w-0">{breadcrumb}</div>
        </>
      )}
    </header>
  );
}
