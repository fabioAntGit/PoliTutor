import { SectionCards } from "@/components/dashboard/section-cards"
import { ChartAreaInteractive } from "@/components/dashboard/chart-area-interactive"
import { DashboardPageHeader } from "@/components/dashboard/dashboard-page-header"
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
        <DashboardPageHeader title="Visão Geral" />

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
