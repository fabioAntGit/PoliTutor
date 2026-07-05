import { Outlet } from "react-router"
import { AppSidebar } from "@/components/dashboard/app-sidebar"
import { UserMenu } from "@/components/account/user-menu"
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar"

export default function DashboardLayout() {
  return (
    <SidebarProvider defaultOpen={false}>
      <AppSidebar />
      <SidebarInset>
        <div className="fixed right-4 top-2.5 z-30">
          <UserMenu compact />
        </div>
        <Outlet />
      </SidebarInset>
    </SidebarProvider>
  )
}