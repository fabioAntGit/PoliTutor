import * as React from "react"
import { NavLink, useLocation } from "react-router"
import { NavMain } from "@/components/dashboard/nav-main"
import { NavSecondary } from "@/components/dashboard/nav-secondary"
import { NavUser } from "@/components/dashboard/nav-user"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarGroupContent,
} from "@/components/ui/sidebar"
import { Skeleton } from "@/components/ui/skeleton"
import {
  LayoutDashboardIcon,
  BookOpenIcon,
  GraduationCapIcon,
} from "lucide-react"
import { useSidebarCourses } from "@/hooks/dashboard/useSidebarCourses"

const user = {
  name: "Professor",
  email: "professor@estg.ipp.pt",
  avatar: "",
}

const navMain = [
  { title: "Visão Geral", url: "/dashboard", icon: <LayoutDashboardIcon />, end: true },
]

const navSecondary: { title: string; url: string; icon: React.ReactNode }[] = []

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const { pathname } = useLocation()
  const { courses } = useSidebarCourses()

  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              asChild
              className="data-[slot=sidebar-menu-button]:p-1.5!"
            >
              <NavLink to="/dashboard">
                <GraduationCapIcon className="size-5!" />
                <span className="text-base font-semibold">Poli Tutor</span>
              </NavLink>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarContent>
        <NavMain items={navMain} />

        {/* Courses section */}
        <SidebarGroup>
          <SidebarGroupLabel>Cursos</SidebarGroupLabel>
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

        <NavSecondary items={navSecondary} className="mt-auto" />
      </SidebarContent>

      <SidebarFooter>
        <NavUser user={user} />
      </SidebarFooter>
    </Sidebar>
  )
}
