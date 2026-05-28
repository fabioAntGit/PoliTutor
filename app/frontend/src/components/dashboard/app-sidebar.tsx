import * as React from "react"
import { NavLink, useLocation } from "react-router"
import { NavMain } from "@/components/dashboard/nav-main"
import { AppShellSidebar } from "@/components/layout/app-shell-sidebar"
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarGroupContent,
} from "@/components/ui/sidebar"
import { Skeleton } from "@/components/ui/skeleton"
import { LayoutDashboardIcon, BookOpenIcon } from "lucide-react"
import { useSidebarCourses } from "@/hooks/dashboard/useSidebarCourses"

const navMain = [
  { title: "Visão Geral", url: "/dashboard", icon: <LayoutDashboardIcon />, end: true },
]

export function AppSidebar({ ...props }: React.ComponentProps<typeof AppShellSidebar>) {
  const { pathname } = useLocation()
  const { courses } = useSidebarCourses()

  return (
    <AppShellSidebar homeTo="/dashboard" {...props}>
      <NavMain items={navMain} />

      <SidebarGroup>
        <SidebarGroupLabel>Cadeiras</SidebarGroupLabel>
        <SidebarGroupContent>
          <SidebarMenu>
            {courses === null ? (
              <>
                <Skeleton className="mx-2 h-7 w-4/5" />
                <Skeleton className="mx-2 mt-1 h-7 w-3/5" />
              </>
            ) : courses.length === 0 ? null : (
              courses.map((course) => {
                const url = `/dashboard/courses/${encodeURIComponent(course)}`
                const isActive = pathname === url
                return (
                  <SidebarMenuItem key={course}>
                    <SidebarMenuButton asChild isActive={isActive} tooltip={course}>
                      <NavLink to={url}>
                        <BookOpenIcon />
                        <span>{course}</span>
                      </NavLink>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                )
              })
            )}
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>
    </AppShellSidebar>
  )
}
