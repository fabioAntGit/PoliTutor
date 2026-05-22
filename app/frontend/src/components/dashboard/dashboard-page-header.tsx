import type { ReactNode } from "react";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";

interface DashboardPageHeaderProps {
  title: ReactNode;
  titleClassName?: string;
}

export function DashboardPageHeader({ title, titleClassName }: DashboardPageHeaderProps) {
  return (
    <header className="flex h-12 shrink-0 items-center gap-2 border-b px-4 lg:px-6">
      <SidebarTrigger className="-ml-1" />
      <Separator
        orientation="vertical"
        className="mx-2 data-[orientation=vertical]:h-4"
      />
      <span className={titleClassName ?? "text-sm font-medium"}>{title}</span>
    </header>
  );
}
