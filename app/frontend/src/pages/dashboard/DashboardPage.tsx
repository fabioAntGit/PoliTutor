import { SidebarTrigger } from "@/components/ui/sidebar"
import { Separator } from "@/components/ui/separator"
import { SectionCards } from "@/components/dashboard/section-cards"
import { ChartAreaInteractive } from "@/components/dashboard/chart-area-interactive"
import { PageState } from "@/components/ui/page-state"
import { useDashboard } from "@/hooks/dashboard/useDashboard"

export default function DashboardPage() {
  const { overview, loading, error } = useDashboard()

  const today = new Date().toLocaleDateString("pt-PT", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  })

  return (
    <PageState loading={loading} error={error}>
      <div className="flex flex-1 flex-col overflow-y-auto">
        <header className="flex h-12 shrink-0 items-center gap-2 border-b px-4 lg:px-6">
          <SidebarTrigger className="-ml-1" />
          <Separator orientation="vertical" className="mx-2 data-[orientation=vertical]:h-4" />
          <span className="text-sm font-medium">Visão Geral</span>
        </header>

        <div className="@container/main flex flex-1 flex-col gap-6 px-4 py-6 lg:px-6">
          <div>
            <h1 className="text-xl font-semibold tracking-tight">Visão Geral</h1>
            <p className="mt-0.5 text-sm text-muted-foreground">{today}</p>
          </div>

          <SectionCards data={overview} />

          <ChartAreaInteractive />
        </div>
      </div>
    </PageState>
  )
}
