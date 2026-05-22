import { useNavigate } from "react-router"
import { Flame, FileText, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { SectionCards } from "@/components/dashboard/section-cards"
import { ChartAreaInteractive } from "@/components/dashboard/chart-area-interactive"
import { DashboardPageHeader } from "@/components/dashboard/dashboard-page-header"
import {
  RankedListCard,
  type RankedListItem,
} from "@/components/dashboard/ranked-list-card"
import { useCourseDashboard } from "@/hooks/dashboard/useCourseDashboard"

export default function CourseDashboardPage() {
  const navigate = useNavigate()
  const { courseId, status, overview, topics, sources } = useCourseDashboard()

  if (status === "not_found") {
    return (
      <div className="flex flex-1 flex-col overflow-y-auto">
        <DashboardPageHeader title="Curso não encontrado" />
        <div className="flex flex-1 flex-col items-center justify-center gap-4 px-4">
          <AlertCircle className="h-12 w-12 text-muted-foreground" />
          <div className="text-center">
            <h1 className="text-lg font-semibold">Curso não encontrado</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              O curso <span className="font-mono font-medium">"{courseId}"</span> não existe ou ainda não tem dados.
            </p>
          </div>
          <Button variant="outline" onClick={() => navigate("/dashboard")}>
            Voltar à Visão Geral
          </Button>
        </div>
      </div>
    )
  }

  const isLoading = status === "loading"
  const topicItems: RankedListItem[] | null = topics
    ? topics.map(({ topic, count }) => ({
        key: topic,
        label: topic,
        value: count,
        valueLabel: `${count}×`,
      }))
    : null
  const sourceItems: RankedListItem[] | null = sources
    ? sources.map(({ filename, references }) => ({
        key: filename,
        label: filename,
        rawLabel: filename,
        value: references,
        valueLabel: `${references} ref.`,
      }))
    : null

  return (
    <div className="flex flex-1 flex-col overflow-y-auto">
      <DashboardPageHeader
        title={<span className="truncate">{courseId ?? "Curso"}</span>}
      />

      <div className="@container/main flex flex-1 flex-col gap-6 px-4 py-6 lg:px-6">
        <div>
          <h1 className="text-xl font-semibold tracking-tight truncate">
            {courseId?.toUpperCase()}
          </h1>
          <p className="mt-0.5 text-sm text-muted-foreground">Análise individual do curso</p>
        </div>

        <SectionCards data={overview} variant="course" />

        <ChartAreaInteractive course={courseId} description="Evolução das perguntas dos alunos neste curso" />

        <div className="grid grid-cols-1 gap-6 @3xl/main:grid-cols-2">
          <RankedListCard
            icon={<Flame className="h-4 w-4 text-orange-500" />}
            title="Conceitos em Destaque"
            description="Conceitos mais abordados pelos alunos nas interações"
            items={topicItems}
            isLoading={isLoading}
            barClassName="bg-primary/50"
          />
          <RankedListCard
            icon={<FileText className="h-4 w-4 text-blue-500" />}
            title="Fontes Mais Consultadas"
            description="Materiais do curso mais citados pelo tutor nas respostas aos alunos"
            items={sourceItems}
            isLoading={isLoading}
            barClassName="bg-blue-500/40"
          />
        </div>
      </div>
    </div>
  )
}
