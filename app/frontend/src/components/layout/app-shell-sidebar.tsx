import * as React from "react";

import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarRail,
} from "@/components/ui/sidebar";

type AppShellSidebarProps = React.ComponentProps<typeof Sidebar>;

export function AppShellSidebar({ children, ...props }: AppShellSidebarProps) {
  return (
    <Sidebar collapsible="offcanvas" {...props}>
      <SidebarHeader>
        <div className="flex items-center gap-2 px-1 py-1">
          <img
            src="/logo.jpg"
            alt="Logótipo da ESTG"
            className="h-8 w-8 shrink-0 rounded-md object-cover"
          />
          <span className="text-base font-semibold">PoliTutor</span>
        </div>
      </SidebarHeader>

      <SidebarContent>{children}</SidebarContent>

      <SidebarRail />
    </Sidebar>
  );
}
