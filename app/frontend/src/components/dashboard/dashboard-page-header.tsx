import { SidebarTrigger } from "@/components/ui/sidebar";

interface DashboardPageHeaderProps {}

export function DashboardPageHeader({}: DashboardPageHeaderProps = {}) {
  return (
    <header className="flex h-12 shrink-0 items-center gap-2 border-b px-4 lg:px-6">
      <SidebarTrigger className="-ml-1" />
      <span className="text-base font-semibold">PoliTutor</span>
    </header>
  );
}
