import * as React from "react";
import { NavLink } from "react-router";
import { GraduationCapIcon } from "lucide-react";

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { UserMenu } from "@/components/account/user-menu";

interface AppShellSidebarProps extends React.ComponentProps<typeof Sidebar> {
  homeTo?: string;
}

export function AppShellSidebar({
  homeTo = "/",
  children,
  ...props
}: AppShellSidebarProps) {
  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              asChild
              className="data-[slot=sidebar-menu-button]:p-1.5!"
            >
              <NavLink to={homeTo}>
                <GraduationCapIcon className="size-5!" />
                <span className="text-base font-semibold">Poli Tutor</span>
              </NavLink>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarContent>{children}</SidebarContent>

      <SidebarFooter>
        <UserMenu />
      </SidebarFooter>
    </Sidebar>
  );
}
