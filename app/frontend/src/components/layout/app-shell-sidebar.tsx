import * as React from "react";

import {
  Sidebar,
  SidebarContent,
  SidebarRail,
} from "@/components/ui/sidebar";

type AppShellSidebarProps = React.ComponentProps<typeof Sidebar>;

export function AppShellSidebar({ children, ...props }: AppShellSidebarProps) {
  return (
    <Sidebar collapsible="offcanvas" {...props}>
      <SidebarContent>{children}</SidebarContent>

      <SidebarRail />
    </Sidebar>
  );
}
